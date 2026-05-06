# A1-5 Attribution Report

## Method
- Model: LinearRegression on standardized feature space.
- Global importance: normalized absolute coefficients.
- Local explanation: SHAP-like linear contributions.

## Top Global Drivers
- metric_avg: 0.5000
- metric_max: 0.5000
- segment_numeric: 0.0000
- event_attendance_window_sum: 0.0000
- hour_of_day: 0.0000
- metric_expected_attendance: 0.0000
- source_event: 0.0000
- grid_D: 0.0000

## Artifacts
- attribution_summary.json
- shap_like_values.csv
- model_card.md