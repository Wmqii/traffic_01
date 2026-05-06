from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd


def _precision_recall_f1(y_true: Sequence[int], y_pred: Sequence[int]) -> Tuple[float, float, float]:
    y_true_arr = np.array(y_true, dtype=int)
    y_pred_arr = np.array(y_pred, dtype=int)
    tp = int(((y_true_arr == 1) & (y_pred_arr == 1)).sum())
    fp = int(((y_true_arr == 0) & (y_pred_arr == 1)).sum())
    fn = int(((y_true_arr == 1) & (y_pred_arr == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    feature_path = root / "data-pipeline/features/output/feature_table.csv"
    out_dir = root / "model/congestion_rules/output"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(feature_path)
    quantile_candidates = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]

    rules: List[Dict[str, float]] = []
    pred_rows: List[Dict[str, object]] = []

    for metric_name, group in df.groupby("metric_name"):
        values = group["metric_sum"].astype(float)
        y_true = (values >= values.quantile(0.80)).astype(int)

        best = {"f1": -1.0, "quantile": 0.75, "threshold": float(values.quantile(0.75)), "precision": 0.0, "recall": 0.0}
        for q in quantile_candidates:
            threshold = float(values.quantile(q))
            y_pred = (values >= threshold).astype(int)
            p, r, f1 = _precision_recall_f1(y_true, y_pred)
            if f1 > best["f1"]:
                best = {"f1": f1, "quantile": q, "threshold": threshold, "precision": p, "recall": r}

        rules.append(
            {
                "metric_name": metric_name,
                "quantile": float(best["quantile"]),
                "threshold": float(best["threshold"]),
                "precision": float(best["precision"]),
                "recall": float(best["recall"]),
                "f1": float(best["f1"]),
                "sample_size": int(len(group)),
            }
        )

        final_pred = (values >= float(best["threshold"]))
        for idx, flag in zip(group.index.tolist(), final_pred.tolist()):
            pred_rows.append(
                {
                    "row_index": int(idx),
                    "metric_name": metric_name,
                    "metric_sum": float(df.loc[idx, "metric_sum"]),
                    "rule_hit": int(flag),
                    "threshold": float(best["threshold"]),
                }
            )

    rule_df = pd.DataFrame(rules).sort_values("f1", ascending=False).reset_index(drop=True)
    pred_df = pd.DataFrame(pred_rows).sort_values("row_index").reset_index(drop=True)

    rule_map = {r["metric_name"]: r["threshold"] for r in rules}
    y_true_all = (df["metric_sum"].astype(float) >= df.groupby("metric_name")["metric_sum"].transform(lambda x: x.quantile(0.80))).astype(int)
    y_pred_all = (df.apply(lambda r: float(r["metric_sum"]) >= float(rule_map[r["metric_name"]]), axis=1)).astype(int)
    p_all, r_all, f1_all = _precision_recall_f1(y_true_all.tolist(), y_pred_all.tolist())

    config_payload = {
        "version": "a1-4-v1.0",
        "method": "quantile_grid_search",
        "rules": rule_df.to_dict(orient="records"),
    }
    eval_payload = {
        "overall": {"precision": p_all, "recall": r_all, "f1": f1_all, "sample_size": int(len(df))},
        "per_metric": rule_df.to_dict(orient="records"),
    }

    (out_dir / "calibration_config.json").write_text(json.dumps(config_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "rule_evaluation.json").write_text(json.dumps(eval_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    pred_df.to_csv(out_dir / "rule_predictions.csv", index=False)

    report = [
        "# A1-4 Congestion Rule Calibration Report",
        "",
        "## Method",
        "- Use metric-specific quantile grid search (0.60 ~ 0.90).",
        "- Pseudo label = top 20% metric_sum by metric_name.",
        "",
        "## Overall",
        f"- Precision: {p_all:.4f}",
        f"- Recall: {r_all:.4f}",
        f"- F1: {f1_all:.4f}",
        "",
        "## Artifacts",
        "- calibration_config.json",
        "- rule_evaluation.json",
        "- rule_predictions.csv",
    ]
    (out_dir / "rule_report.md").write_text("\n".join(report), encoding="utf-8")

    print("Saved congestion rule artifacts: calibration_config.json, rule_evaluation.json, rule_predictions.csv")
    print(json.dumps(eval_payload["overall"], ensure_ascii=False))


if __name__ == "__main__":
    main()
