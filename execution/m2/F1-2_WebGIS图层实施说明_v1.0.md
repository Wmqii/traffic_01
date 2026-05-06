# F1-2 WebGIS 图层实施说明 v1.0

## 1. 任务目标

- 在前端实现可交互 WebGIS 能力，支持热力、事件、路段三类图层。
- 与后端热力层与事件接口联动，形成地图与图表联动基础。

## 2. 技术选型

- 地图库：Leaflet 1.9.4（CDN）
- 底图：OpenStreetMap
- 图层组织：Leaflet `LayerGroup`

## 3. 实施内容

1. 地图容器与初始化
- 在 `frontend/index.html` 新增 `#map` 容器（实时页面）。
- 在 `frontend/assets/app.js` 初始化地图中心与缩放级别。

2. 图层模型
- `heat` 图层：根据 `GET /api/v1/map/layers/heat` 的 `heat_score` 绘制圆点，半径与颜色映射拥堵热度。
- `events` 图层：根据 `GET /api/v1/congestion/events` 绘制事件点，并展示事件名/路段/等级。
- `segments` 图层：按预置路段几何绘制折线，颜色随热度分值变化。

3. 交互控制
- 左侧新增图层开关：`热力图层 / 事件图层 / 路段图层`。
- 开关状态实时控制 `LayerGroup` 显隐。

4. API 失败降级
- 若热力或事件接口不可用，自动切到 Mock 图层数据。
- 降级行为写入运行日志，便于门禁测试和验收回溯。

## 4. 交付文件

- `frontend/index.html`
- `frontend/assets/app.js`
- `frontend/assets/styles.css`
- `frontend/README.md`

## 5. 后续扩展建议

- 增加真实路网 GeoJSON/矢量瓦片接入，替代当前演示路段几何。
- 支持图层时间轴播放、聚合点渲染与圈选查询。
- 与后端新增 `map/layers/segments` 接口后，可移除前端硬编码路段坐标。
