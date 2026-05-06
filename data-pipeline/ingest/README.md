# Data Ingest Skeleton

This folder holds the minimal ingestion scaffold described in the task. Each component is intentionally simple so it can be extended later.

## Layout
- `config/data_sources.sample.yaml` shows how to declare taxi, metro, weather, and event inputs.
- `schemas/*.json` defines the minimal column schema for each source so downstream jobs know what fields to expect.
- `samples/*.csv` contains three rows per source that conform to the schemas.
- `scripts/ingest_runner.py` copies every sample CSV into `staging/` and writes `staging/ingest_report.json` summarizing the copy.
- `staging/` is the destination for ingested CSVs and the runtime report; it is intentionally empty in the repo so the script can populate it.

## Requirements
- Python 3.9+ (the script only uses the standard library).

## Running the sample ingestion
1. Open a shell and change into this directory:
   ```
   cd d:\小桌面\交通拥堵\data-pipeline\ingest
   ```
2. Execute the runner:
   ```
   python scripts/ingest_runner.py
   ```
3. After the script finishes, check `staging/` for the copied CSVs and open `staging/ingest_report.json` to inspect counts and timestamps.

Feel free to swap in real sources by updating `samples/`, aligning the files with the JSON schemas, and adding config entries as needed.
