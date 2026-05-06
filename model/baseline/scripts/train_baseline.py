"""Train and evaluate the A1-1 baseline models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

try:
    import xgboost as _xgb

    TREE_MODEL_BASE = _xgb.XGBRegressor
    TREE_MODEL_NAME = "xgboost.XGBRegressor"
    TREE_DEPENDENCY = "xgboost"
    TREE_KWARGS = {"n_estimators": 100, "random_state": 42, "verbosity": 0}
except ModuleNotFoundError:
    from sklearn.ensemble import GradientBoostingRegressor as _skgb

    TREE_MODEL_BASE = _skgb
    TREE_MODEL_NAME = "sklearn.GradientBoostingRegressor"
    TREE_DEPENDENCY = "sklearn.GradientBoostingRegressor (fallback for missing xgboost)"
    TREE_KWARGS = {"n_estimators": 100, "random_state": 42}


def parse_args() -> argparse.Namespace:
    script_root = Path(__file__).resolve().parent
    repo_root = script_root.parents[2]
    default_features = repo_root / "data-pipeline" / "features" / "output" / "feature_table.csv"
    default_output = repo_root / "model" / "baseline" / "output"

    parser = argparse.ArgumentParser(
        description="Train the A1-1 baseline models and emit evaluation artifacts."
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=default_features,
        help="Path to the feature table produced by the feature pipeline.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output,
        help="Directory where metrics, predictions, and report files are written.",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.75,
        help="Fraction of rows reserved for training (the remainder forms validation).",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="metric_sum",
        help="Target column for regression (default is metric_sum).",
    )
    return parser.parse_args()


def _safe_train_split(length: int, ratio: float) -> tuple[int, int]:
    ratio = min(max(ratio, 0.05), 0.95)
    train_size = int(length * ratio)
    train_size = max(1, min(train_size, length - 1))
    val_size = length - train_size
    return train_size, val_size


def _compute_metrics(actual: Sequence[float], preds: Sequence[float]) -> dict[str, float]:
    actual_arr = np.array(actual, dtype=float)
    preds_arr = np.array(preds, dtype=float)
    if actual_arr.size == 0:
        return {"rmse": float("nan"), "mae": float("nan"), "mape": float("nan")}
    mask = ~np.isnan(actual_arr)
    actual_arr = actual_arr[mask]
    preds_arr = preds_arr[mask]
    rmse = float(np.sqrt(np.mean((actual_arr - preds_arr) ** 2)))
    mae = float(np.mean(np.abs(actual_arr - preds_arr)))
    safe_denominator = np.maximum(np.abs(actual_arr), 1e-8)
    mape = float(np.mean(np.abs(actual_arr - preds_arr) / safe_denominator) * 100)
    return {"rmse": rmse, "mae": mae, "mape": mape}


def _prepare_tree_features(df: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    df = df.copy()
    numeric_fields = [
        "metric_avg",
        "metric_max",
        "metric_count",
        "hour_of_day",
        "day_of_week",
        "is_weekend",
        "is_peak_hour",
        "segment_numeric",
        "event_attendance_window_sum",
        "weather_precip_window_avg",
        "lag1_metric_sum",
    ]
    for field in numeric_fields:
        df[field] = pd.to_numeric(df.get(field, 0), errors="coerce").fillna(0.0)

    for cat in ["metric_name", "grid_area"]:
        if cat not in df.columns:
            df[cat] = "missing"
        else:
            df[cat] = df[cat].fillna("missing").astype(str)

    cat_dummies = pd.get_dummies(df[["metric_name", "grid_area"]], drop_first=False)
    feature_df = pd.concat([df[numeric_fields], cat_dummies], axis=1)
    feature_df = feature_df.fillna(0.0)
    target_series = pd.to_numeric(df[target_col], errors="coerce").fillna(0.0)
    return feature_df, target_series, list(feature_df.columns)


def _write_predictions(predictions: pd.DataFrame, path: Path) -> None:
    predictions.to_csv(path, index=False)


def _write_metrics(metrics: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8") as handler:
        json.dump(metrics, handler, indent=2, ensure_ascii=False)


def _generate_report(
    path: Path,
    total_rows: int,
    train_rows: int,
    val_rows: int,
    unique_windows: int,
    train_windows: int,
    val_windows: int,
    arima_metrics: dict[str, float],
    tree_metrics: dict[str, float],
) -> None:
    report_lines: list[str] = [
        "# A1-1 Baseline模型训练与评估报告",
        "",
        "## 数据概况",
        f"- 特征行数：{total_rows}",
        f"- 训练集行数：{train_rows}",
        f"- 验证集行数：{val_rows}",
        f"- 唯一时间窗口：{unique_windows}",
        f"- 训练窗口：{train_windows}",
        f"- 验证窗口：{val_windows}",
        "",
        "## 模型信息",
        f"- ARIMA(order=(1,1,1))：基于聚合的 `metric_sum` 时间序列。",
        f"- 树模型：{TREE_MODEL_NAME}（依赖 `{TREE_DEPENDENCY}`）。",
        "",
        "## 验证指标",
        "| 模型 | RMSE | MAE | MAPE(%) |",
        "| --- | --- | --- | --- |",
        f"| ARIMA | {arima_metrics['rmse']:.4f} | {arima_metrics['mae']:.4f} | {arima_metrics['mape']:.2f} |",
        f"| 树模型 | {tree_metrics['rmse']:.4f} | {tree_metrics['mae']:.4f} | {tree_metrics['mape']:.2f} |",
        "",
        "## 观测与说明",
        "- 树模型使用跨 `metric_name` 与 `grid_area` 的 one-hot 特征输入，保留 `lag1_metric_sum` 作为自回归参考。",
        "- ARIMA 以统一时间窗口 `window_start` 构建的聚合 `metric_sum` 序列建模，可作为全局基线。",
        "",
        "## 输出产物",
        "- `metrics.json`",
        "- `predictions.csv`",
        "- `model_report.md`",
    ]
    if TREE_DEPENDENCY != "xgboost":
        report_lines.insert(
            report_lines.index("## 输出产物"),
            "- 由于 `xgboost` 未安装，树模型采用 `sklearn.GradientBoostingRegressor` 回退。",
        )
    path.write_text("\n".join(report_lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    features_path = args.features
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(features_path, parse_dates=["window_start", "window_end"])
    df = df.sort_values("window_start").reset_index(drop=True)
    total_rows = len(df)
    train_rows, val_rows = _safe_train_split(total_rows, args.train_ratio)
    split_idx = train_rows
    train_df = df.iloc[:split_idx]
    val_df = df.iloc[split_idx:]

    ts = (
        df.groupby("window_start")
        .agg(metric_sum=("metric_sum", "sum"), window_end=("window_end", "max"))
        .sort_index()
    )
    ts.index = pd.to_datetime(ts.index)
    if ts.index.tz is not None:
        ts.index = ts.index.tz_convert(None)
    ts["window_end"] = pd.to_datetime(ts["window_end"])
    if ts["window_end"].dt.tz is not None:
        ts["window_end"] = ts["window_end"].dt.tz_convert(None)

    unique_windows = len(ts)
    window_train_rows, _ = _safe_train_split(unique_windows, args.train_ratio)
    window_split_idx = window_train_rows
    window_train_ts = ts.iloc[:window_split_idx]
    window_val_ts = ts.iloc[window_split_idx:]

    arima_metrics: dict[str, float] = {"rmse": float("nan"), "mae": float("nan"), "mape": float("nan")}
    arima_predictions = pd.Series(dtype=float)
    if len(window_val_ts) > 0:
        arima_model = ARIMA(window_train_ts["metric_sum"], order=(1, 1, 1))
        arima_fit = arima_model.fit()
        forecast = arima_fit.get_forecast(steps=len(window_val_ts))
        arima_predictions = forecast.predicted_mean
        arima_predictions.index = window_val_ts.index
        arima_metrics = _compute_metrics(window_val_ts["metric_sum"], arima_predictions)

    feature_df, target_series, _ = _prepare_tree_features(df, args.target)
    train_features = feature_df.iloc[:split_idx]
    val_features = feature_df.iloc[split_idx:]
    y_train = target_series.iloc[:split_idx]
    y_val = target_series.iloc[split_idx:]

    tree_model = TREE_MODEL_BASE(**TREE_KWARGS)
    tree_model.fit(train_features, y_train)
    tree_preds = tree_model.predict(val_features)
    tree_metrics = _compute_metrics(y_val, tree_preds)

    tree_pred_df = val_df[["window_start", "window_end", "segment_id", "metric_name"]].copy()
    tree_pred_df["model"] = "tree"
    tree_pred_df["actual"] = y_val.to_numpy()
    tree_pred_df["prediction"] = tree_preds

    arima_pred_df = pd.DataFrame(
        {
            "window_start": window_val_ts.index,
            "window_end": window_val_ts["window_end"],
            "segment_id": "aggregated",
            "metric_name": "aggregated_metric_sum",
            "actual": window_val_ts["metric_sum"].to_numpy(),
            "prediction": arima_predictions.to_numpy(),
            "model": "arima",
        }
    )

    predictions = pd.concat([tree_pred_df, arima_pred_df], ignore_index=True)
    predictions = predictions[
        ["model", "window_start", "window_end", "segment_id", "metric_name", "actual", "prediction"]
    ]

    metrics_payload = {
        "dataset": {
            "total_rows": total_rows,
            "train_rows": train_rows,
            "val_rows": val_rows,
            "unique_windows": unique_windows,
            "train_windows": len(window_train_ts),
            "val_windows": len(window_val_ts),
            "feature_table": str(features_path.resolve()),
        },
        "models": {
            "arima": {
                "order": [1, 1, 1],
                "metrics": arima_metrics,
            },
            "tree": {
                "type": TREE_MODEL_NAME,
                "dependency": TREE_DEPENDENCY,
                "metrics": tree_metrics,
            },
        },
    }

    predictions_path = output_dir / "predictions.csv"
    metrics_path = output_dir / "metrics.json"
    report_path = output_dir / "model_report.md"
    _write_predictions(predictions, predictions_path)
    _write_metrics(metrics_payload, metrics_path)
    _generate_report(
        report_path,
        total_rows,
        train_rows,
        val_rows,
        unique_windows,
        len(window_train_ts),
        len(window_val_ts),
        arima_metrics,
        tree_metrics,
    )

    print("Saved predictions.csv, metrics.json, and model_report.md to the baseline output directory.")
    print(f"Tree model ({TREE_MODEL_NAME}) metrics: {tree_metrics}")
    print(f"ARIMA metrics: {arima_metrics}")


if __name__ == "__main__":
    main()
