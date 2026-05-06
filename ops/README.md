# O1-2 Deployment Guide (dev/test/prod)

## 1. Scope

- Start/stop backend + frontend for `dev/test/prod`.
- Environment variable isolation via `ops/environments/*.env`.
- Smoke verification for health/auth/RBAC chain.

## 2. Files

- Env templates:
  - `ops/environments/dev.env`
  - `ops/environments/test.env`
  - `ops/environments/prod.env`
- Runtime scripts:
  - `ops/scripts/start_env.ps1`
  - `ops/scripts/stop_env.ps1`
  - `ops/scripts/deploy_env.ps1`
  - `ops/scripts/smoke_api.ps1`
- Optional container templates:
  - `ops/docker/docker-compose.dev.yml`
  - `ops/docker/docker-compose.test.yml`
  - `ops/docker/docker-compose.prod.yml`

## 3. Quick Start

```powershell
cd d:\小桌面\交通拥堵
.\ops\scripts\deploy_env.ps1 -EnvName dev -NoInstall
```

Outputs:
- API URL
- Frontend URL
- runtime pid file: `ops/runtime/dev.pids.json`
- smoke artifact: `ops/artifacts/o1_2_smoke_dev.json`

## 4. Stop Environment

```powershell
cd d:\小桌面\交通拥堵
.\ops\scripts\stop_env.ps1 -EnvName dev
```

## 5. Smoke Only

```powershell
cd d:\小桌面\交通拥堵
.\ops\scripts\smoke_api.ps1 -EnvName test
```

## 6. Rollback

1. Stop current env:
```powershell
.\ops\scripts\stop_env.ps1 -EnvName <dev|test|prod>
```
2. Restore previous artifact/config version (if tracked externally).
3. Re-run deploy:
```powershell
.\ops\scripts\deploy_env.ps1 -EnvName <dev|test|prod> -NoInstall
```

## 7. Monitoring Check (O1-3)

```powershell
cd d:\小桌面\交通拥堵
.\ops\scripts\monitoring_check.ps1 -EnvName dev
```

Artifacts:
- `ops/artifacts/o1_3_monitor_dev.json`
- `ops/artifacts/o1_3_monitor_dashboard_dev.json`

## 8. Gray Release Drill (O1-4)

```powershell
cd d:\小桌面\交通拥堵
.\ops\scripts\gray_release_drill.ps1 -EnvName dev -NoInstall
```

Artifact:
- `ops/artifacts/o1_4_gray_release_drill_dev.json`

## 9. Runbook + Incident Drill (O1-5)

```powershell
cd d:\小桌面\交通拥堵
.\ops\scripts\o1_5_runbook_drill.ps1 -EnvName dev -NoInstall
```

Artifacts:
- `ops/artifacts/o1_5_runbook_drill_dev.json`
- `ops/runbooks/o1_5_runbook_v1.0.md`
- `ops/runbooks/o1_5_incident_plan_v1.0.md`
