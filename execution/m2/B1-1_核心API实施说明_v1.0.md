# B1-1 核心 API 实施说明 v1.0

## 目标与边界

- 本实施专注于 `backend/` 目录下的 FastAPI 服务（B1-1 范围），提供预测、事件、成因及热图接口，完全以本地产物为数据源，不依赖外部服务。
- 保持运行脚本和 OpenAPI 导出在 `backend/` 目录，验证记录在 `execution/m2/` 区域存档，以便与其他 Agent 并行。

## 架构概览

1. **数据源**  
   - `data-pipeline/features/output/feature_table.csv`：提供分段指标统计（如 `expected_attendance`、`occupancy_pct` 等）；
   - `data-pipeline/alignment/output/aligned/aligned_records.csv`：用于定位事件和对齐实体；
   - `data-pipeline/quality/output/quality_scoreboard.csv`：用于构造置信度/评分反馈，提升 `confidence` 计算。

2. **核心组件：`backend/data.py`**  
   - 采用 `csv.DictReader` 加载三类产出，转换为结构化的 `datetime`、`float` 等字段，避免重复解析；
   - `DataRepository` 维护索引（按 `segment_id` 聚合特征行）和指标最大值，用于计算热图分数和 impact；
   - 包含 `get_segment_predictions`、`list_congestion_events`、`get_event_attribution`、`get_heat_layer` 等方法，直接供 API 层调用。

3. **FastAPI 服务：`backend/app.py`**  
   - 定义接口：  
     * `GET /api/v1/predictions/segments/{segment_id}`：返回该段最近窗口的预测、置信度、特征摘要；  
     * `GET /api/v1/congestion/events`：输出对齐事件的观测级 severity/confidence；  
     * `GET /api/v1/attributions/events/{event_id}`：列出对事件最有贡献的特征驱动项；  
     * `GET /api/v1/map/layers/heat`：基于 `metric_avg` 计算热分数；  
     * `GET /health`：提供心跳检查；  
   - 所有响应均通过 Pydantic 模型/字段校验，确保 `confidence`、`heat_score` 等在合理范围；
   - 启用了 `openapi_url`/`docs_url`/`redoc_url`，方便其他 Agent 调用。

4. **OpenAPI 输出**  
   - `backend/export_openapi.py`：加载 `app.openapi()` 并写入 `backend/openapi.json`，脚本顺序叙述在 `backend/README.md`，便于代码生成或自动化验证。

5. **运行说明**  
   - 依赖 `fastapi`、`uvicorn`、`pydantic`，可通过 `pip install fastapi uvicorn pydantic` 安装；
   - 服务器启动：`uvicorn backend.app:app --reload --port 8000`（README 也说明了 `/api/v1/docs`）；
   - OpenAPI 导出：`python backend/export_openapi.py` 生成 `backend/openapi.json`，供下游消费。

## 异常与扩展考虑

- 数据加载在模块初始化阶段完成，失败会抛出 `FileNotFoundError`；后续可考虑增加缓存层或支持 JSON 格式；
- 当前 attribution 顺序是根据 impact 排序并截断前 6 项，适配后续 UI 展示；
- 如需对接真实预测模型，可将 `DataRepository` 替换为实际模型推理层，只需保持接口契约。
