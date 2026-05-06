# Frontend（改版后业务展示）

## 页面结构
- 路况总览：地图路段拥堵状态 + 路段流量对比 + 单路段时间趋势
- 拥堵归因：天气/节假日/交通事故贡献趋势与排序
- 流量预测：未来流量、历史真实值对比、误差（MAE/MAPE/RMSE）
- 数据说明：口径、分级规则、交互说明

## 启动方式
```powershell
cd d:\小桌面\交通拥堵
$env:PYTHONPATH='.'
uvicorn backend.app:app --port 8005

cd d:\小桌面\交通拥堵\frontend
python -m http.server 5500
```

访问：`http://127.0.0.1:5500`

## 接口依赖（免登录）
- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/segments/{segment_id}/trend`
- `GET /api/v1/analytics/segments/{segment_id}/causes`
- `GET /api/v1/analytics/segments/{segment_id}/prediction`
- `GET /api/v1/analytics/predictions/segments`
- `GET /api/v1/analytics/models/errors`
- `GET /api/v1/analytics/segments/{segment_id}/report`
- `GET /api/v1/map/layers/heat`
- `GET /api/v1/map/segments/geometry`
- `GET /api/v1/map/segments/geometry/meta`
- `GET /api/v1/congestion/events`
- `GET /api/v1/predictions/segments/{segment_id}`

## 真实路网对齐（可选）
- 前端会优先请求 `GET /api/v1/map/segments/geometry` 作为路段几何。
- 后端默认读取：`data-pipeline/alignment/config/segment_geometry.json`。
- 若该文件不存在，则回退到内置演示几何线。
- 可参考样例文件：`data-pipeline/alignment/config/segment_geometry.sample.json`。

## S3 回归测试
```powershell
cd d:\小桌面\交通拥堵
$env:PYTHONPATH='.'
python backend/tests/api_automation_runner.py
python frontend/tests/revamp_e2e_runner.py
```

## 验证产物
- `execution/revamp/output/s1_s2_api_smoke_result.json`
- `execution/revamp/output/s1_s2_frontend_check_result.json`
- `backend/tests/output/t1_2_api_test_result.json`
- `frontend/tests/output/revamp_e2e_result.json`
