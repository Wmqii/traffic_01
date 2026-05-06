# 日志留痕规范

## 1. 目标
- 保证多 Agent 执行全过程可追踪、可审计、可复盘。

## 2. 文件说明
- `worklog.csv`：日常任务执行日志（每个 Agent 每日最少1条）
- `testlog.csv`：测试执行与门禁结论日志（每次测试必填）
- `releaselog.csv`：部署、发布、回滚、配置变更日志（每次变更必填）

## 3. 填报规则
- 时间统一使用 `YYYY-MM-DD HH:mm:ss`（Asia/Shanghai）。
- `evidence_path` 填测试报告、截图、流水线链接或文档路径。
- 状态枚举：
  - worklog: `To Do|In Progress|Blocked|Done`
  - testlog: `PASS|FAIL|BLOCKED`
  - releaselog: `SUCCESS|FAILED|ROLLBACK`

## 4. 审核规则
- 每天 18:00 前由各 Agent 更新 worklog。
- 每阶段门禁前，Test-Agent 汇总 testlog 并输出门禁结论。
- 发布后 1 小时内，Ops-Agent 完成 releaselog 归档。
