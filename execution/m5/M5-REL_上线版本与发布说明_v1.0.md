# M5-REL 上线版本与发布说明（v1.0）

## 1. 文档信息
- 文档编号：`M5-REL`
- 版本：`v1.0`
- 日期：`2026-03-27`
- 责任 Agent：`PM-Agent`
- 阶段：`M5`

## 2. 发布范围
- 前端：驾驶舱、联动分析、高级图表、导出中心（F1-1~F1-5）
- 后端：核心 API、鉴权、缓存与异步任务、调度接口、审计与错误码（B1-1~B1-5）
- 模型：深度模型推理、版本管理与回滚（A1-2/A1-6）
- 运维：监控告警、灰度回滚、运行手册与应急预案（O1-3~O1-5）

## 3. 发布版本信息
- 发布版本：`traffic-m5-v1.0`
- 发布环境：`test -> prod（按发布窗口推进）`
- 基线来源：
  - `M5-UAT` 验收通过
  - `M5` 文档与验收链路完整

## 4. 变更摘要
1. 新增模型调度与回滚能力（重训/发布/回滚/健康）。
2. 增强审计日志与标准错误码，支持统一追踪。
3. 完成监控、灰度、应急演练闭环并形成运行手册。
4. 完成 UAT 验收文档与项目复盘材料归档。

## 5. 上线前检查清单
- [x] UAT 验收报告通过（`M5-UAT`）
- [x] 发布前门禁通过（M4/M5 对应 testlog 全绿）
- [x] 上线回滚方案明确（O1-4 + A1-6）
- [x] 运行手册与应急预案可执行（O1-5）
- [x] 审计与错误码规范可追踪（B1-5）

## 6. 发布步骤
1. 锁定发布窗口与变更冻结。
2. 执行部署与 smoke：
```powershell
.\ops\scripts\deploy_env.ps1 -EnvName test -NoInstall
.\ops\scripts\smoke_api.ps1 -EnvName test
```
3. 执行监控与灰度演练校验：
```powershell
.\ops\scripts\monitoring_check.ps1 -EnvName test
.\ops\scripts\gray_release_drill.ps1 -EnvName test -NoInstall
```
4. 执行上线确认并归档发布清单。

## 7. 回滚策略
- 应用回滚：执行 `stop/start + smoke + monitor`。
- 模型回滚：调用 `POST /api/v1/tasks/model/rollback` 指定目标版本。
- 回滚触发条件：
  - 核心接口成功率低于 99%
  - P95 指标超过阈值
  - 出现 critical 告警

## 8. 发布后观察
- 观察窗口：`24h`
- 关键指标：
  - API 可用性与 P95
  - 监控告警数量（critical/warning）
  - 错误码分布与审计事件增长趋势

## 9. 关联文件
- `execution/m5/M5-UAT_验收报告_v1.0.md`
- `execution/m5/C1-4_验收报告与项目复盘_v1.0.md`
- `ops/artifacts/m5_release_manifest_v1.json`
- `execution/m5/M5-REL_验证记录_2026-03-27.md`

