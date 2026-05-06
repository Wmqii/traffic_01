# D1-3 Alignment Runner

Map matching and time-window alignment based on D1-2 clean outputs.

## Input
- `data-pipeline/governance/output/clean/*.csv`
- `config/spatial_mapping.json`

## Output
- `output/aligned/aligned_records.csv`
- `output/alignment_report.json`
- `config/segment_geometry.json` (optional, for real road geometry overlay)

## Run
```powershell
cd d:\小桌面\交通拥堵\data-pipeline\alignment
python .\scripts\alignment_runner.py
```

## Real Road Geometry Import (Optional)
Use this when you have real road network geometry and want map lines aligned to real roads.

### 1) From GeoJSON (LineString / MultiLineString)
```powershell
cd d:\小桌面\交通拥堵\data-pipeline\alignment
python .\scripts\segment_geometry_builder.py --geojson .\config\road_segments.geojson --segment-id-field segment_id
```

### 2) From CSV
CSV required fields:
- `segment_id`
- `coordinates` (e.g. `31.226,121.459;31.229,121.466`)

```powershell
cd d:\小桌面\交通拥堵\data-pipeline\alignment
python .\scripts\segment_geometry_builder.py --csv .\config\road_segments.csv --segment-id-field segment_id --coordinates-field coordinates --csv-coord-order latlng
```

### 3) Output
- Writes to `config/segment_geometry.json`
- Backend API `GET /api/v1/map/segments/geometry` will then use this file first.

Template:
- `config/segment_geometry.sample.json`
