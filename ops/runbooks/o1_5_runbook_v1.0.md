# O1-5 运行手册（v1.0）

## 1. 文档信息
- 文档编号：`O1-5-RUNBOOK`
- 版本：`v1.0`
- 日期：`2026-03-27`
- 责任 Agent：`Ops-Agent`
- 适用环境：`dev/test/prod`

## 2. 目标与范围
- 为发布前检查、日常巡检、故障恢复提供标准化执行步骤。
- 覆盖系统启动、健康检查、监控巡检、灰度演练、回滚恢复。
- 形成可审计证据（JSON 产物 + 日志记录）。

## 3. 先决条件
- 在项目根目录执行：`d:\小桌面\交通拥堵`
- 可访问 Python 与 PowerShell。
- 环境配置已存在：`ops/environments/<env>.env`

## 4. 常用命令

### 4.1 启动并部署
```powershell
.\ops\scripts\deploy_env.ps1 -EnvName dev -NoInstall
```

### 4.2 停止环境
```powershell
.\ops\scripts\stop_env.ps1 -EnvName dev
```

### 4.3 Smoke 校验
```powershell
.\ops\scripts\smoke_api.ps1 -EnvName dev
```

### 4.4 监控巡检
```powershell
.\ops\scripts\monitoring_check.ps1 -EnvName dev
```

### 4.5 灰度回滚演练
```powershell
.\ops\scripts\gray_release_drill.ps1 -EnvName dev -NoInstall
```

### 4.6 O1-5 一体化运行手册演练
```powershell
.\ops\scripts\o1_5_runbook_drill.ps1 -EnvName dev -NoInstall
```

## 5. 值班巡检清单
- `runtime` 文件存在且 PID 存活。
- `GET /health` 返回 200。
- viewer/admin 登录与 RBAC 链路正常。
- `map/layers/heat` 可访问。
- 模型指标文件存在且新鲜度达标。
- `backend.err.log` 未超过告警阈值。

## 6. 发布前门禁清单
- `smoke_api` 通过（6/6）。
- `monitoring_check` 通过（critical=0）。
- `gray_release_drill` 通过（4/4）。
- 本次变更已写入 `execution/logs/releaselog.csv`。

## 7. 回滚流程
1. 执行 `stop_env.ps1` 停止当前服务。
2. 恢复上一个稳定版本（代码/配置/模型）。
3. 执行 `start_env.ps1` 启动环境。
4. 执行 `smoke_api.ps1` 与 `monitoring_check.ps1` 验证恢复成功。

## 8. 证据归档
- 巡检产物：`ops/artifacts/o1_3_monitor_<env>.json`
- 灰度演练：`ops/artifacts/o1_4_gray_release_drill_<env>.json`
- 运行手册演练：`ops/artifacts/o1_5_runbook_drill_<env>.json`

