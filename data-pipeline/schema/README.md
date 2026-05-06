# Core Database Schema (M2 Addendum)

## Scope
- Core dimensions: region, grid, segment.
- Core facts: traffic metric, congestion event.
- Model artifacts: prediction and attribution tables.
- Index + range partition design for 15-minute windows.

## Files
- DDL: `data-pipeline/schema/output/core_schema_ddl.sql`
- Checker: `data-pipeline/schema/scripts/schema_check.py`
- Check result: `data-pipeline/schema/output/schema_check_result.json`

## Check
```powershell
cd d:\小桌面\交通拥堵
python data-pipeline/schema/scripts/schema_check.py
```
