# D1-2 Governance Runner

This directory contains the minimal governance pipeline for D1-2 checks:
- anomaly detection
- missing field detection
- duplicate detection
- delayed record detection

## Structure
- `config/governance_rules.json`: source-level rules.
- `scripts/governance_runner.py`: executes governance checks.
- `output/clean/*.csv`: accepted records by source.
- `output/rejects/*_rejects.csv`: rejected records with reasons.
- `output/governance_report.json`: run summary.

## Run
```powershell
cd d:\小桌面\交通拥堵\data-pipeline\governance
python .\scripts\governance_runner.py
```

## Demo Rule Verification
```powershell
python .\scripts\governance_runner.py --demo-anomalies
```

