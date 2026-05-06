# D1-4 Feature Engineering

Feature generation based on aligned records from D1-3.

## Input
- `data-pipeline/alignment/output/aligned/aligned_records.csv`
- `config/feature_spec.json`

## Output
- `output/feature_table.csv`
- `output/feature_report.json`

## Run
```powershell
cd d:\小桌面\交通拥堵\data-pipeline\features
python .\scripts\feature_runner.py
```

