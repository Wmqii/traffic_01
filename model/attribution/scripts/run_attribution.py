from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    feature_path = root / "data-pipeline/features/output/feature_table.csv"
    rules_path = root / "model/congestion_rules/output/calibration_config.json"
    out_dir = root / "model/attribution/output"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(feature_path)

    numeric_cols = [
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
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    cat_df = pd.get_dummies(df[["source", "metric_name", "grid_area"]].astype(str), prefix=["source", "metric", "grid"])
    x_df = pd.concat([df[numeric_cols], cat_df], axis=1)
    x = x_df.to_numpy(dtype=float)
    y = pd.to_numeric(df["metric_sum"], errors="coerce").fillna(0.0).to_numpy(dtype=float)

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)

    model = LinearRegression()
    model.fit(x_scaled, y)

    coef = model.coef_
    feature_names = x_df.columns.tolist()

    global_raw = np.abs(coef)
    global_norm = global_raw / np.sum(global_raw) if np.sum(global_raw) > 0 else global_raw

    global_df = pd.DataFrame({"feature": feature_names, "importance": global_norm})
    global_df = global_df.sort_values("importance", ascending=False).reset_index(drop=True)

    pred = model.predict(x_scaled)
    scored = df.copy()
    scored["pred_score"] = pred
    top = scored.sort_values("pred_score", ascending=False).head(20).copy()

    # Local SHAP-like values (linear contribution on standardized features)
    centered = x_scaled - np.mean(x_scaled, axis=0, keepdims=True)
    local_vals = centered * coef

    top_rows = []
    for _, row in top.iterrows():
        idx = int(row.name)
        contrib = local_vals[idx]
        local_df = pd.DataFrame({"feature": feature_names, "contribution": contrib})
        local_df = local_df.sort_values("contribution", ascending=False)
        for _, r in local_df.head(8).iterrows():
            top_rows.append(
                {
                    "row_index": idx,
                    "segment_id": row["segment_id"],
                    "metric_name": row["metric_name"],
                    "feature": r["feature"],
                    "contribution": float(r["contribution"]),
                }
            )

    shap_like_df = pd.DataFrame(top_rows)
    shap_like_df.to_csv(out_dir / "shap_like_values.csv", index=False)

    rules = {}
    if rules_path.exists():
        payload = json.loads(rules_path.read_text(encoding="utf-8"))
        for item in payload.get("rules", []):
            rules[str(item.get("metric_name"))] = float(item.get("threshold", 0.0))

    sample_explanations: List[Dict[str, object]] = []
    for _, row in top.head(5).iterrows():
        metric_name = str(row["metric_name"])
        threshold = float(rules.get(metric_name, 0.0))
        sample_explanations.append(
            {
                "segment_id": row["segment_id"],
                "metric_name": metric_name,
                "pred_score": float(row["pred_score"]),
                "rule_threshold": threshold,
                "rule_hit": bool(float(row["metric_sum"]) >= threshold) if threshold > 0 else False,
                "top_driver": shap_like_df[shap_like_df["row_index"] == int(row.name)]["feature"].head(1).tolist(),
            }
        )

    summary = {
        "version": "a1-5-v1.0",
        "model": "linear_regression_shap_like",
        "sample_size": int(len(df)),
        "global_top_features": global_df.head(10).to_dict(orient="records"),
        "sample_explanations": sample_explanations,
    }
    (out_dir / "attribution_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# A1-5 Attribution Report",
        "",
        "## Method",
        "- Model: LinearRegression on standardized feature space.",
        "- Global importance: normalized absolute coefficients.",
        "- Local explanation: SHAP-like linear contributions.",
        "",
        "## Top Global Drivers",
    ]
    for _, r in global_df.head(8).iterrows():
        report.append(f"- {r['feature']}: {float(r['importance']):.4f}")

    report += [
        "",
        "## Artifacts",
        "- attribution_summary.json",
        "- shap_like_values.csv",
        "- model_card.md",
    ]
    (out_dir / "model_card.md").write_text("\n".join(report), encoding="utf-8")

    print("Saved attribution artifacts: attribution_summary.json, shap_like_values.csv, model_card.md")
    print(json.dumps({"sample_size": summary["sample_size"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
