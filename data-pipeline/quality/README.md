# D1-5 Data Quality Monitoring

Quality scoring layer for the M2 data pipeline.

## Input
- `data-pipeline/ingest/staging/ingest_report.json`
- `data-pipeline/governance/output/governance_report_normal.json`
- `data-pipeline/alignment/output/alignment_report.json`
- `data-pipeline/features/output/feature_table.csv`
- `config/quality_rules.json`

## Output
- `output/quality_scoreboard.csv`
- `output/quality_report.json`
- `output/quality_dashboard_echarts.json`

## Run
```powershell
cd d:\小桌面\交通拥堵\data-pipeline\quality
python .\scripts\quality_runner.py
```

