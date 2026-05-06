"""Train and evaluate A1-2 deep models (LSTM/GRU) with robust fallback."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


def parse_args() -> argparse.Namespace:
    script_root = Path(__file__).resolve().parent
    repo_root = script_root.parents[2]
    default_features = repo_root / "data-pipeline" / "features" / "output" / "feature_table.csv"
    default_output = repo_root / "model" / "deep" / "output"

    parser = argparse.ArgumentParser(description="Train LSTM/GRU models for A1-2 and emit artifacts.")
    parser.add_argument("--features", type=Path, default=default_features)
    parser.add_argument("--output-dir", type=Path, default=default_output)
    parser.add_argument("--seq-len", type=int, default=3)
    parser.add_argument("--train-ratio", type=float, default=0.75)
    parser.add_argument("--epochs", type=int, default=80)
    return parser.parse_args()


def compute_metrics(actual: Sequence[float], pred: Sequence[float]) -> Dict[str, float]:
    actual_arr = np.array(actual, dtype=float)
    pred_arr = np.array(pred, dtype=float)
    rmse = float(np.sqrt(mean_squared_error(actual_arr, pred_arr)))
    mae = float(mean_absolute_error(actual_arr, pred_arr))
    safe = np.maximum(np.abs(actual_arr), 1e-8)
    mape = float(np.mean(np.abs(actual_arr - pred_arr) / safe) * 100)
    return {"rmse": rmse, "mae": mae, "mape": mape}


def safe_split(length: int, ratio: float) -> Tuple[int, int]:
    ratio = min(max(ratio, 0.5), 0.95)
    train_size = int(length * ratio)
    train_size = max(1, min(train_size, length - 1))
    val_size = length - train_size
    return train_size, val_size


def build_window_table(df: pd.DataFrame) -> pd.DataFrame:
    base = (
        df.groupby("window_start")
        .agg(
            window_end=("window_end", "max"),
            target_metric_sum=("metric_sum", "sum"),
            event_attendance_window_sum=("event_attendance_window_sum", "sum"),
            weather_precip_window_avg=("weather_precip_window_avg", "mean"),
            is_peak_hour=("is_peak_hour", "max"),
            is_weekend=("is_weekend", "max"),
        )
        .sort_index()
    )

    metric_pivot = (
        df.pivot_table(
            index="window_start",
            columns="metric_name",
            values="metric_sum",
            aggfunc="sum",
            fill_value=0.0,
        )
        .sort_index()
    )
    metric_pivot.columns = [f"metric_{col}" for col in metric_pivot.columns]

    result = base.join(metric_pivot, how="left").fillna(0.0)
    return result


def make_sequences(table: pd.DataFrame, seq_len: int) -> Tuple[np.ndarray, np.ndarray, List[pd.Timestamp]]:
    feature_cols = [c for c in table.columns if c not in {"window_end", "target_metric_sum"}]
    feat = table[feature_cols].to_numpy(dtype=float)
    target = table["target_metric_sum"].to_numpy(dtype=float)
    idx = table.index.to_list()

    xs: List[np.ndarray] = []
    ys: List[float] = []
    target_windows: List[pd.Timestamp] = []
    for i in range(seq_len, len(table)):
        xs.append(feat[i - seq_len : i, :])
        ys.append(target[i])
        target_windows.append(idx[i])

    if not xs:
        raise ValueError("Not enough windows to build sequence samples. Lower --seq-len or add more data.")

    return np.array(xs, dtype=float), np.array(ys, dtype=float), target_windows


def train_with_tensorflow(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_scaler: StandardScaler,
    epochs: int,
) -> Tuple[np.ndarray, np.ndarray, str]:
    import tensorflow as tf
    from tensorflow import keras

    tf.random.set_seed(42)
    np.random.seed(42)

    seq_len = x_train.shape[1]
    n_features = x_train.shape[2]

    def build_model(kind: str) -> keras.Model:
        model = keras.Sequential(name=f"{kind}_model")
        model.add(keras.layers.Input(shape=(seq_len, n_features)))
        if kind == "lstm":
            model.add(keras.layers.LSTM(32))
        else:
            model.add(keras.layers.GRU(32))
        model.add(keras.layers.Dense(16, activation="relu"))
        model.add(keras.layers.Dense(1))
        model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.01), loss="mse")
        return model

    callbacks = [keras.callbacks.EarlyStopping(monitor="loss", patience=10, restore_best_weights=True)]
    batch_size = max(1, min(8, len(x_train)))

    lstm_model = build_model("lstm")
    lstm_model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0, callbacks=callbacks)
    lstm_pred_scaled = lstm_model.predict(x_val, verbose=0).reshape(-1, 1)

    gru_model = build_model("gru")
    gru_model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0, callbacks=callbacks)
    gru_pred_scaled = gru_model.predict(x_val, verbose=0).reshape(-1, 1)

    lstm_pred = y_scaler.inverse_transform(lstm_pred_scaled).reshape(-1)
    gru_pred = y_scaler.inverse_transform(gru_pred_scaled).reshape(-1)
    return lstm_pred, gru_pred, "tensorflow.keras"


def train_with_fallback(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_scaler: StandardScaler,
) -> Tuple[np.ndarray, np.ndarray, str]:
    x_train_flat = x_train.reshape(x_train.shape[0], -1)
    x_val_flat = x_val.reshape(x_val.shape[0], -1)

    lstm_like = MLPRegressor(hidden_layer_sizes=(64, 32), random_state=42, max_iter=1200)
    lstm_like.fit(x_train_flat, y_train)
    lstm_pred_scaled = lstm_like.predict(x_val_flat).reshape(-1, 1)

    gru_like = MLPRegressor(hidden_layer_sizes=(48, 24), random_state=43, max_iter=1200)
    gru_like.fit(x_train_flat, y_train)
    gru_pred_scaled = gru_like.predict(x_val_flat).reshape(-1, 1)

    lstm_pred = y_scaler.inverse_transform(lstm_pred_scaled).reshape(-1)
    gru_pred = y_scaler.inverse_transform(gru_pred_scaled).reshape(-1)
    return lstm_pred, gru_pred, "sklearn.MLPRegressor(fallback)"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.features, parse_dates=["window_start", "window_end"])
    df = df.sort_values("window_start").reset_index(drop=True)
    table = build_window_table(df)

    x, y, sample_windows = make_sequences(table, seq_len=args.seq_len)

    train_size, val_size = safe_split(len(x), args.train_ratio)
    x_train, x_val = x[:train_size], x[train_size:]
    y_train, y_val = y[:train_size], y[train_size:]
    win_val = sample_windows[train_size:]

    n_features = x.shape[2]
    x_scaler = StandardScaler()
    x_scaler.fit(x_train.reshape(-1, n_features))

    def transform_x(arr: np.ndarray) -> np.ndarray:
        flat = arr.reshape(-1, n_features)
        scaled = x_scaler.transform(flat)
        return scaled.reshape(arr.shape)

    x_train_scaled = transform_x(x_train)
    x_val_scaled = transform_x(x_val)

    y_scaler = StandardScaler()
    y_train_scaled = y_scaler.fit_transform(y_train.reshape(-1, 1)).reshape(-1)

    backend_used = ""
    used_fallback = False
    try:
        lstm_pred, gru_pred, backend_used = train_with_tensorflow(
            x_train_scaled, y_train_scaled, x_val_scaled, y_scaler, args.epochs
        )
    except Exception:
        used_fallback = True
        lstm_pred, gru_pred, backend_used = train_with_fallback(
            x_train_scaled, y_train_scaled, x_val_scaled, y_scaler
        )

    lstm_metrics = compute_metrics(y_val, lstm_pred)
    gru_metrics = compute_metrics(y_val, gru_pred)

    pred_df = pd.DataFrame(
        {
            "window_start": win_val,
            "actual": y_val,
            "lstm_prediction": lstm_pred,
            "gru_prediction": gru_pred,
        }
    )
    pred_df["window_start"] = pd.to_datetime(pred_df["window_start"])
    predictions_long = pd.concat(
        [
            pred_df.assign(model="lstm", prediction=pred_df["lstm_prediction"]),
            pred_df.assign(model="gru", prediction=pred_df["gru_prediction"]),
        ],
        ignore_index=True,
    )[["model", "window_start", "actual", "prediction"]]

    metrics_payload = {
        "dataset": {
            "feature_table": str(args.features.resolve()),
            "raw_rows": int(len(df)),
            "window_rows": int(len(table)),
            "sequence_length": int(args.seq_len),
            "sample_count": int(len(x)),
            "train_samples": int(train_size),
            "val_samples": int(val_size),
            "feature_count": int(n_features),
        },
        "runtime": {
            "backend": backend_used,
            "used_fallback": used_fallback,
        },
        "models": {
            "lstm": {"metrics": lstm_metrics},
            "gru": {"metrics": gru_metrics},
        },
    }

    metrics_path = args.output_dir / "metrics.json"
    predictions_path = args.output_dir / "predictions.csv"
    report_path = args.output_dir / "model_report.md"

    metrics_path.write_text(json.dumps(metrics_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    predictions_long.to_csv(predictions_path, index=False)

    report_lines = [
        "# A1-2 深度模型训练评估报告",
        "",
        "## 数据概况",
        f"- 原始特征行数: {len(df)}",
        f"- 时间窗聚合行数: {len(table)}",
        f"- 序列长度: {args.seq_len}",
        f"- 样本总数: {len(x)}",
        f"- 训练样本: {train_size}",
        f"- 验证样本: {val_size}",
        "",
        "## 模型与运行后端",
        f"- 运行后端: {backend_used}",
        f"- 是否回退: {'是' if used_fallback else '否'}",
        "",
        "## 验证指标",
        "| 模型 | RMSE | MAE | MAPE(%) |",
        "| --- | --- | --- | --- |",
        f"| LSTM | {lstm_metrics['rmse']:.4f} | {lstm_metrics['mae']:.4f} | {lstm_metrics['mape']:.2f} |",
        f"| GRU | {gru_metrics['rmse']:.4f} | {gru_metrics['mae']:.4f} | {gru_metrics['mape']:.2f} |",
        "",
        "## 输出产物",
        "- metrics.json",
        "- predictions.csv",
        "- model_report.md",
    ]
    if used_fallback:
        report_lines.append("- 说明: tensorflow/keras 不可用或训练失败，已回退为 sklearn.MLPRegressor。")

    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print("Saved deep-model artifacts: metrics.json, predictions.csv, model_report.md")
    print(json.dumps(metrics_payload["models"], ensure_ascii=False))


if __name__ == "__main__":
    main()
