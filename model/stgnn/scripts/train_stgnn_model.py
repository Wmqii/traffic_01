from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error


def _metrics(actual: Sequence[float], pred: Sequence[float]) -> Dict[str, float]:
    a = np.array(actual, dtype=float)
    p = np.array(pred, dtype=float)
    rmse = float(np.sqrt(mean_squared_error(a, p)))
    mae = float(mean_absolute_error(a, p))
    den = np.maximum(np.abs(a), 1e-8)
    mape = float(np.mean(np.abs(a - p) / den) * 100)
    return {"rmse": rmse, "mae": mae, "mape": mape}


def _build_neighbors(values: np.ndarray, radius: int = 2) -> Dict[int, np.ndarray]:
    neighbors: Dict[int, np.ndarray] = {}
    for i, v in enumerate(values):
        mask = np.where(np.abs(values - v) <= radius)[0]
        mask = mask[mask != i]
        neighbors[i] = mask
    return neighbors


def _safe_split(n: int, ratio: float = 0.75) -> Tuple[int, int]:
    train = max(1, min(int(n * ratio), n - 1))
    return train, n - train


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    feature_path = root / "data-pipeline/features/output/feature_table.csv"
    out_dir = root / "model/stgnn/output"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(feature_path, parse_dates=["window_start", "window_end"])
    df = df.sort_values(["window_start", "segment_id"]).reset_index(drop=True)

    agg = (
        df.groupby(["window_start", "segment_id", "segment_numeric"], as_index=False)
        .agg(
            target=("metric_sum", "sum"),
            event_attendance=("event_attendance_window_sum", "sum"),
            precip=("weather_precip_window_avg", "mean"),
            is_peak=("is_peak_hour", "max"),
            is_weekend=("is_weekend", "max"),
        )
    )

    agg["lag_target"] = agg.groupby("segment_id")["target"].shift(1)
    # Fallback for sparse segment history: use global window lag when segment lag is missing.
    agg["global_lag_target"] = agg["target"].shift(1)
    agg["lag_target"] = agg["lag_target"].fillna(agg["global_lag_target"]).fillna(0.0)
    agg["hour"] = agg["window_start"].dt.hour

    work = agg.copy()
    work = work.sort_values(["window_start", "segment_id"]).reset_index(drop=True)

    seg_vals = work["segment_numeric"].to_numpy(dtype=float)
    neighbor_map = _build_neighbors(seg_vals, radius=2)

    target_values = work["target"].to_numpy(dtype=float)
    neigh_mean = []
    for i in range(len(work)):
        idx = neighbor_map[i]
        neigh_mean.append(float(target_values[idx].mean()) if len(idx) else float(target_values[i]))
    work["neighbor_target_mean"] = neigh_mean

    feature_cols = [
        "lag_target",
        "neighbor_target_mean",
        "event_attendance",
        "precip",
        "hour",
        "is_peak",
        "is_weekend",
    ]

    x = work[feature_cols].fillna(0.0).to_numpy(dtype=float)
    y = work["target"].to_numpy(dtype=float)

    train_n, _ = _safe_split(len(work), 0.75)
    x_train, x_val = x[:train_n], x[train_n:]
    y_train, y_val = y[:train_n], y[train_n:]

    model = Ridge(alpha=1.0, random_state=42)
    model.fit(x_train, y_train)
    pred = model.predict(x_val)

    m = _metrics(y_val, pred)

    pred_df = work.iloc[train_n:][["window_start", "segment_id"]].copy()
    pred_df["actual"] = y_val
    pred_df["prediction"] = pred
    pred_df.to_csv(out_dir / "predictions.csv", index=False)

    payload = {
        "dataset": {
            "feature_table": str(feature_path),
            "raw_rows": int(len(df)),
            "samples": int(len(work)),
            "train_samples": int(train_n),
            "val_samples": int(len(work) - train_n),
            "segment_count": int(work["segment_id"].nunique()),
        },
        "graph": {
            "radius": 2,
            "avg_neighbor_count": float(np.mean([len(v) for v in neighbor_map.values()])) if neighbor_map else 0.0,
        },
        "model": {
            "type": "stgnn_proxy_ridge",
            "feature_columns": feature_cols,
            "metrics": m,
        },
    }
    (out_dir / "metrics.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# A1-3 STGNN Model Report",
        "",
        "## Dataset",
        f"- Raw rows: {len(df)}",
        f"- Samples: {len(work)}",
        f"- Train/Val: {train_n}/{len(work) - train_n}",
        "",
        "## Graph",
        "- Neighbor rule: abs(segment_numeric diff) <= 2",
        f"- Avg neighbor count: {payload['graph']['avg_neighbor_count']:.2f}",
        "",
        "## Metrics",
        f"- RMSE: {m['rmse']:.4f}",
        f"- MAE: {m['mae']:.4f}",
        f"- MAPE: {m['mape']:.2f}%",
        "",
        "## Artifacts",
        "- metrics.json",
        "- predictions.csv",
        "- model_report.md",
    ]
    (out_dir / "model_report.md").write_text("\n".join(report), encoding="utf-8")

    print("Saved STGNN artifacts: metrics.json, predictions.csv, model_report.md")
    print(json.dumps(m, ensure_ascii=False))


if __name__ == "__main__":
    main()
