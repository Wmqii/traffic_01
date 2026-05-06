# A1-2 Deep Models (LSTM/GRU)

This module trains and evaluates sequence models for congestion forecasting.

## Inputs
- Feature table: `data-pipeline/features/output/feature_table.csv`
- Sequence unit: aggregated by `window_start`

## Run
```powershell
cd d:\小桌面\交通拥堵
python model/deep/scripts/train_deep_models.py
```

Optional args:
- `--features`: custom feature table path
- `--output-dir`: output directory (default `model/deep/output`)
- `--seq-len`: sequence length (default `3`)
- `--train-ratio`: train split ratio (default `0.75`)
- `--epochs`: max epochs for tensorflow training (default `80`)

## Dependency behavior
- Preferred backend: `tensorflow.keras` (LSTM/GRU)
- Fallback backend: `sklearn.MLPRegressor`

## Outputs
- `model/deep/output/metrics.json`
- `model/deep/output/predictions.csv`
- `model/deep/output/model_report.md`
