# A1-1 Baseline模型训练与评估报告

## 数据概况
- 特征行数：12
- 训练集行数：9
- 验证集行数：3
- 唯一时间窗口：6
- 训练窗口：4
- 验证窗口：2

## 模型信息
- ARIMA(order=(1,1,1))：基于聚合的 `metric_sum` 时间序列。
- 树模型：sklearn.GradientBoostingRegressor（依赖 `sklearn.GradientBoostingRegressor (fallback for missing xgboost)`）。

## 验证指标
| 模型 | RMSE | MAE | MAPE(%) |
| --- | --- | --- | --- |
| ARIMA | 13163.5022 | 10684.1175 | 119.10 |
| 树模型 | 10872.8372 | 8442.5332 | 99.43 |

## 观测与说明
- 树模型使用跨 `metric_name` 与 `grid_area` 的 one-hot 特征输入，保留 `lag1_metric_sum` 作为自回归参考。
- ARIMA 以统一时间窗口 `window_start` 构建的聚合 `metric_sum` 序列建模，可作为全局基线。

- 由于 `xgboost` 未安装，树模型采用 `sklearn.GradientBoostingRegressor` 回退。
## 输出产物
- `metrics.json`
- `predictions.csv`
- `model_report.md`