#!/usr/bin/env python3
"""Build segment geometry config from GeoJSON or CSV.

Output format:
{
  "segments": [
    {"segment_id": "SEG-1001", "coordinates": [[lat, lng], [lat, lng], ...]}
  ]
}
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
FEATURE_TABLE_PATH = ROOT_DIR.parent / "features" / "output" / "feature_table.csv"
DEFAULT_OUTPUT = ROOT_DIR / "config" / "segment_geometry.json"


def _as_float(value: Any) -> float:
    return float(str(value).strip())


def _normalize_line_points(points: list[list[float]]) -> list[list[float]]:
    normalized: list[list[float]] = []
    for item in points:
        if not isinstance(item, list) or len(item) < 2:
            continue
        lat = _as_float(item[0])
        lng = _as_float(item[1])
        normalized.append([round(lat, 6), round(lng, 6)])
    return normalized


def _geojson_line_to_latlng(geometry: dict[str, Any]) -> list[list[float]]:
    geo_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geo_type == "LineString" and isinstance(coords, list):
        line = []
        for pt in coords:
            if isinstance(pt, list) and len(pt) >= 2:
                lng = _as_float(pt[0])
                lat = _as_float(pt[1])
                line.append([lat, lng])
        return _normalize_line_points(line)
    if geo_type == "MultiLineString" and isinstance(coords, list):
        longest: list[list[float]] = []
        for part in coords:
            if not isinstance(part, list):
                continue
            line = []
            for pt in part:
                if isinstance(pt, list) and len(pt) >= 2:
                    lng = _as_float(pt[0])
                    lat = _as_float(pt[1])
                    line.append([lat, lng])
            if len(line) > len(longest):
                longest = line
        return _normalize_line_points(longest)
    return []


def _parse_csv_coordinates(raw: str, order: str) -> list[list[float]]:
    text = raw.strip()
    if not text:
        return []

    # JSON array: [[lat, lng], ...] or [[lng, lat], ...]
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            points: list[list[float]] = []
            for pt in parsed:
                if isinstance(pt, list) and len(pt) >= 2:
                    a = _as_float(pt[0])
                    b = _as_float(pt[1])
                    if order == "lnglat":
                        points.append([b, a])
                    else:
                        points.append([a, b])
            if points:
                return _normalize_line_points(points)
    except Exception:
        pass

    # Delimited string: "lat,lng;lat,lng;..."
    # Or: "lat lng|lat lng|..."
    separators = [";", "|"]
    chunks = [text]
    for sep in separators:
        if sep in text:
            chunks = [part for part in text.split(sep) if part.strip()]
            break

    points: list[list[float]] = []
    for chunk in chunks:
        cleaned = chunk.replace(",", " ").strip()
        parts = [x for x in cleaned.split() if x]
        if len(parts) < 2:
            continue
        a = _as_float(parts[0])
        b = _as_float(parts[1])
        if order == "lnglat":
            points.append([b, a])
        else:
            points.append([a, b])
    return _normalize_line_points(points)


def build_from_geojson(path: Path, segment_id_field: str) -> dict[str, list[list[float]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", []) if isinstance(payload, dict) else []
    result: dict[str, list[list[float]]] = {}

    for idx, feature in enumerate(features):
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if not isinstance(props, dict) or not isinstance(geometry, dict):
            continue
        seg_id = props.get(segment_id_field) or feature.get("id") or f"SEG-AUTO-{idx+1:04d}"
        if not isinstance(seg_id, str):
            continue
        line = _geojson_line_to_latlng(geometry)
        if len(line) >= 2:
            result[seg_id] = line
    return result


def build_from_csv(path: Path, segment_id_field: str, coordinates_field: str, order: str) -> dict[str, list[list[float]]]:
    result: dict[str, list[list[float]]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            normalized_row = {(k or "").strip().lstrip("\ufeff"): (v or "") for k, v in row.items()}
            seg_id = (normalized_row.get(segment_id_field) or "").strip()
            coords_raw = normalized_row.get(coordinates_field) or ""
            if not seg_id:
                continue
            line = _parse_csv_coordinates(coords_raw, order=order)
            if len(line) >= 2:
                result[seg_id] = line
    return result


def expected_segment_ids() -> set[str]:
    if not FEATURE_TABLE_PATH.exists():
        return set()
    expected: set[str] = set()
    with FEATURE_TABLE_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            seg_id = (row.get("segment_id") or "").strip()
            if seg_id:
                expected.add(seg_id)
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description="Build segment_geometry.json from GeoJSON or CSV.")
    parser.add_argument("--geojson", type=str, help="Input GeoJSON file path.")
    parser.add_argument("--csv", dest="csv_path", type=str, help="Input CSV file path.")
    parser.add_argument("--segment-id-field", type=str, default="segment_id", help="Segment id field name.")
    parser.add_argument("--coordinates-field", type=str, default="coordinates", help="CSV coordinates field name.")
    parser.add_argument(
        "--csv-coord-order",
        type=str,
        default="latlng",
        choices=["latlng", "lnglat"],
        help="Coordinate order in CSV coordinates field.",
    )
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT), help="Output segment_geometry.json path.")
    args = parser.parse_args()

    if not args.geojson and not args.csv_path:
        raise SystemExit("Provide --geojson or --csv.")
    if args.geojson and args.csv_path:
        raise SystemExit("Use one input source at a time: --geojson OR --csv.")

    if args.geojson:
        source_path = Path(args.geojson).resolve()
        geometry = build_from_geojson(source_path, segment_id_field=args.segment_id_field)
        source_kind = "geojson"
    else:
        source_path = Path(args.csv_path).resolve()
        geometry = build_from_csv(
            source_path,
            segment_id_field=args.segment_id_field,
            coordinates_field=args.coordinates_field,
            order=args.csv_coord_order,
        )
        source_kind = "csv"

    if not source_path.exists():
        raise SystemExit(f"Input file not found: {source_path}")
    if not geometry:
        raise SystemExit("No valid segment geometry parsed from input.")

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"segment_id": seg_id, "coordinates": coords} for seg_id, coords in sorted(geometry.items())]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_kind": source_kind,
        "source_file": str(source_path),
        "segments": rows,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    expected = expected_segment_ids()
    covered = set(geometry.keys())
    missing = sorted(expected - covered)
    extra = sorted(covered - expected)

    print(f"segment_geometry_file={output_path.name}")
    print(f"segment_count={len(rows)}")
    if expected:
        print(f"expected_segments={len(expected)}")
        print(f"covered_segments={len(covered & expected)}")
    if missing:
        print(f"missing_segments={','.join(missing)}")
    if extra:
        print(f"extra_segments={','.join(extra)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
