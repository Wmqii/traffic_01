# A1-1 Baseline 模型训练

该脚本实现 A1-1 所需的基线建模：按时间窗拆分特征表，分别训练 ARIMA（statsmodels）与树模型（优先 xgboost，否则退回 sklearn），并产出验证指标与预测。

## 运行前置条件
- Python 3.8 及以上（或兼容的 conda 环境）。
- 依赖包：`pandas`, `numpy`, `statsmodels`。`xgboost` 可选，缺失时会自动退回 `sklearn.GradientBoostingRegressor`（无需额外命令）。

## 快速运行
```powershell
python model/baseline/scripts/train_baseline.py
```

可选参数：

- `--features`: 指定特征表（默认 `data-pipeline/features/output/feature_table.csv`）。
- `--output-dir`: 指定输出目录（默认 `model/baseline/output`）。
- `--train-ratio`: 训练集占比（默认 0.75）。
- `--target`: 回归目标字段（默认 `metric_sum`）。

## 输出内容
- `model/baseline/output/metrics.json`：包含数据切分、ARIMA 与树模型的 RMSE/MAE/MAPE。
- `model/baseline/output/predictions.csv`：验证集的逐行树模型预测与聚合 ARIMA 预测。
- `model/baseline/output/model_report.md`：运行回顾与依赖说明（会注明是否发生 xgboost 回退）。

## 说明
- 树模型以 `metric_name` 与 `grid_area` 的 one-hot 编码、`lag1_metric_sum` 等字段扩展特征。
- ARIMA 基于每个 `window_start` 组合的 `metric_sum` 聚合序列建模，适用于全局趋势对比。
- Statsmodels 可能会对短序列发出警告（无频率、观测过少），属于预期行为，无需额外干预。
