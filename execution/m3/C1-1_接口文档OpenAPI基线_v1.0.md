# C1-1 接口文档 OpenAPI 基线（v1.0）

## 1. 文档信息
- 文档编号：`C1-1`
- 版本：`v1.0`
- 日期：`2026-03-27`
- 责任 Agent：`Doc-Agent`
- 阶段：`M3`

## 2. 基线目标
- 冻结 `B1-3` 之后的接口契约基线，统一后续前后端联调与测试依据。
- 明确接口目录、鉴权矩阵、导出流程与版本治理规则。

## 3. OpenAPI 基线产物
- 文件：`backend/openapi.json`
- 生成命令：

```powershell
cd d:\小桌面\交通拥堵
$env:PYTHONPATH='.'
python backend/export_openapi.py
```

- 基线信息：
  - `info.version`：`0.1.0`
  - `path_count`：`13`
  - `schema_count`：`17`

## 4. 接口目录（v1.0）

| Method | Path | 功能 |
|---|---|---|
| GET | `/health` | 服务健康检查 |
| POST | `/api/v1/auth/login` | 登录获取 JWT |
| GET | `/api/v1/auth/me` | 当前用户信息 |
| GET | `/api/v1/predictions/segments/{segment_id}` | 路段拥堵预测 |
| GET | `/api/v1/congestion/events` | 拥堵事件列表 |
| GET | `/api/v1/attributions/events/{event_id}` | 事件归因详情 |
| GET | `/api/v1/map/layers/heat` | 地图热力图层 |
| GET | `/api/v1/cache/stats` | 缓存统计信息 |
| POST | `/api/v1/cache/refresh/heat` | 同步刷新热力缓存 |
| POST | `/api/v1/tasks/cache/refresh-heat` | 异步提交热力刷新任务 |
| GET | `/api/v1/tasks/{task_id}` | 查询任务状态 |
| GET | `/api/v1/tasks` | 查询任务列表 |
| GET | `/api/v1/admin/audit` | 审计快照 |

## 5. 鉴权与角色矩阵

| 接口范围 | viewer | analyst | admin |
|---|---|---|---|
| `/api/v1/auth/*` | 登录/查看本人 | 登录/查看本人 | 登录/查看本人 |
| 预测/事件/热力查询 | 允许 | 允许 | 允许 |
| 事件归因详情 | 禁止 | 允许 | 允许 |
| 缓存刷新与任务接口 | 禁止 | 允许 | 允许 |
| 缓存统计 `/api/v1/cache/stats` | 禁止 | 禁止 | 允许 |
| 审计接口 `/api/v1/admin/audit` | 禁止 | 禁止 | 允许 |

## 6. 版本与变更治理
- OpenAPI 文件作为接口契约单一来源，存放于 `backend/openapi.json`。
- 任意接口变更需同步执行：
  - 更新后端实现与模型定义；
  - 重新导出 OpenAPI；
  - 运行 `T1-2` 接口自动化测试；
  - 更新 `execution/m3` 文档与评审记录。
- 变更未完成上述步骤不得进入阶段门禁。

## 7. 关联文件
- `backend/export_openapi.py`
- `backend/openapi.json`
- `backend/app.py`
- `execution/m3/C1-1_验证记录_2026-03-27.md`

