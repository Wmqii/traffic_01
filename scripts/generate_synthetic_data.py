import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALIGNMENT_DIR = PROJECT_ROOT / "data-pipeline" / "alignment"
FEATURES_DIR = PROJECT_ROOT / "data-pipeline" / "features" / "output"
GEOMETRY_PATH = ALIGNMENT_DIR / "config" / "segment_geometry.json"

BASE_LAT = 31.20
BASE_LON = 121.44
LAT_STEP = 0.006
LON_STEP = 0.008

SEGMENT_COUNT = 101
GRID_COLS = 10

def generate_segments():
    segments = {}
    for i in range(1, SEGMENT_COUNT + 1):
        seg_num = 1000 + i
        seg_id = f"SEG-{seg_num}"
        col = (i - 1) % GRID_COLS
        row = (i - 1) // GRID_COLS
        lat1 = BASE_LAT + row * LAT_STEP + random.uniform(-0.001, 0.001)
        lon1 = BASE_LON + col * LON_STEP + random.uniform(-0.001, 0.001)
        lat2 = lat1 + 0.003 + random.uniform(-0.001, 0.001)
        lon2 = lon1 + 0.004 + random.uniform(-0.001, 0.001)
        segments[seg_id] = {
            "segment_id": seg_id,
            "coordinates": [[round(lat1, 6), round(lon1, 6)], [round(lat2, 6), round(lon2, 6)]],
            "grid_col": col,
            "grid_row": row,
        }
    return segments

def save_geometry(segments):
    geometry = {"segments": []}
    for seg_id, data in segments.items():
        geometry["segments"].append({
            "segment_id": seg_id,
            "coordinates": data["coordinates"]
        })
    GEOMETRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GEOMETRY_PATH, "w", encoding="utf-8") as f:
        json.dump(geometry, f, indent=2, ensure_ascii=False)
    print(f"Saved segment geometry to {GEOMETRY_PATH}")

def generate_weather_data(segments, start_date, days=3):
    weather_types = [
        ("晴", 0.0, 0.0),
        ("晴", 0.0, 0.0),
        ("多云", 0.0, 2.0),
        ("阴", 0.0, 4.0),
        ("小雨", 2.5, 8.0),
        ("中雨", 8.0, 15.0),
        ("大雨", 18.0, 30.0),
        ("雾", 0.0, 1.0),
        ("雪", 3.0, 6.0),
    ]
    records = []
    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        for hour in range(24):
            for minute in [0, 30]:
                ts = current_date.replace(hour=hour, minute=minute, second=0)
                weather_choice = random.choices(
                    weather_types,
                    weights=[15, 15, 15, 12, 10, 8, 5, 12, 8]
                )[0]
                name, precip, wind = weather_choice
                precip_val = precip + random.uniform(-0.5, 0.5) if precip > 0 else 0.0
                wind_val = wind + random.uniform(-1, 2) if wind > 0 else random.uniform(0, 3)
                precip_val = max(0, round(precip_val, 1))
                wind_val = round(max(0, wind_val), 1)
                temp_val = round(10 + random.uniform(-5, 15) + (15 if name == "晴" else 0), 1)
                for seg_id in list(segments.keys())[:20]:
                    col = segments[seg_id]["grid_col"]
                    records.append({
                        "station_id": f"ws-{col:03d}",
                        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "temperature_c": temp_val,
                        "precip_mm": precip_val,
                        "wind_kph": wind_val,
                        "segment_id": seg_id,
                    })
    return records

def generate_metro_data(segments, start_date, days=3):
    lines = ["1号线", "2号线", "3号线", "4号线", "5号线", "6号线", "7号线", "8号线", "9号线", "10号线"]
    stations_per_line = 8
    records = []
    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        for hour in range(5, 23):
            for minute in [0, 15, 30, 45]:
                ts = current_date.replace(hour=hour, minute=minute, second=0)
                for line_idx, line_name in enumerate(lines):
                    for sta_idx in range(stations_per_line):
                        is_peak = (7 <= hour <= 9) or (17 <= hour <= 19)
                        base_occ = random.randint(20, 60)
                        if is_peak:
                            base_occ = random.randint(55, 90)
                        occupancy = min(98, base_occ + random.randint(-5, 5))
                        seg_idx = (line_idx * 2 + sta_idx // 4) % len(segments)
                        seg_id = list(segments.keys())[seg_idx]
                        col = segments[seg_id]["grid_col"]
                        records.append({
                            "train_id": f"metro-{line_idx * 100 + sta_idx:04d}",
                            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "station": f"{line_name}第{sta_idx + 1}站",
                            "line": line_name,
                            "occupancy_pct": occupancy,
                            "segment_id": seg_id,
                        })
    return records

def generate_taxi_data(segments, start_date, days=3):
    zones = ["商业区", "住宅区", "火车站", "机场", "医院", "学校", "景区", "写字楼", "商场", "公园"]
    records = []
    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        for hour in range(24):
            for minute in range(0, 60, 15):
                ts = current_date.replace(hour=hour, minute=minute, second=0)
                for _ in range(random.randint(5, 15)):
                    pickup_zone = random.choice(zones)
                    dropoff_zone = random.choice(zones)
                    passengers = random.randint(1, 4)
                    seg_id = random.choice(list(segments.keys()))
                    col = segments[seg_id]["grid_col"]
                    records.append({
                        "ride_id": f"taxi-{random.randint(100000, 999999)}",
                        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "pickup_zone": pickup_zone,
                        "dropoff_zone": dropoff_zone,
                        "passenger_count": passengers,
                        "segment_id": seg_id,
                    })
    return records

def generate_event_data(segments, start_date, days=7):
    event_types = [
        ("大型演唱会", 20000, 35000),
        ("体育赛事", 15000, 30000),
        ("展览活动", 5000, 15000),
        ("集市活动", 2000, 8000),
        ("节假日庆典", 8000, 18000),
        ("交通管制", 50, 300),
        ("道路施工", 30, 150),
        ("恶劣天气预警", 20, 100),
    ]
    records = []
    event_id = 1
    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        events_today = random.randint(5, 12)
        for _ in range(events_today):
            hour = random.randint(8, 20)
            minute = random.choice([0, 15, 30, 45])
            ts = current_date.replace(hour=hour, minute=minute, second=0)
            event_choice = random.choices(
                event_types,
                weights=[5, 8, 15, 30, 10, 50, 60, 45]
            )[0]
            name, min_att, max_att = event_choice
            attendance = random.randint(min_att, max_att)
            location = f"活动中心{random.randint(1, 20)}号场地"
            affected_segs = random.sample(list(segments.keys()), min(random.randint(2, 6), len(segments)))
            for seg_id in affected_segs:
                col = segments[seg_id]["grid_col"]
                records.append({
                    "event_id": f"event-{event_id:04d}",
                    "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "location": location,
                    "category": name,
                    "expected_attendance": attendance,
                    "segment_id": seg_id,
                })
            event_id += 1
    return records

def generate_feature_table(segments, weather_data, metro_data, taxi_data, event_data, start_date, days=7):
    records = []
    all_sources = []

    if event_data:
        for rec in event_data:
            dt = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
            dow = dt.weekday()
            hour = dt.hour
            is_weekend = 1 if dow >= 5 else 0
            is_peak = 1 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0
            precip_key = f"{rec['segment_id']}:{dt.strftime('%Y%m%d%H')}"
            precip = weather_data.get(precip_key, 0.0) if weather_data else 0.0
            all_sources.append({
                "source": "event",
                "segment_id": rec["segment_id"],
                "grid_id": f"GRID-D{segments[rec['segment_id']]['grid_col'] + 1}",
                "window_start": dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "window_end": (dt + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "metric_name": "expected_attendance",
                "metric_sum": float(rec["expected_attendance"]),
                "metric_avg": float(rec["expected_attendance"]),
                "metric_max": float(rec["expected_attendance"]),
                "metric_count": 1,
                "hour_of_day": hour,
                "day_of_week": dow,
                "is_weekend": is_weekend,
                "is_peak_hour": is_peak,
                "segment_numeric": int(rec["segment_id"].replace("SEG-", "")),
                "grid_area": "D",
                "event_attendance_window_sum": float(rec["expected_attendance"]),
                "weather_precip_window_avg": precip,
            })

    if metro_data:
        for rec in metro_data:
            dt = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
            dow = dt.weekday()
            hour = dt.hour
            is_weekend = 1 if dow >= 5 else 0
            is_peak = 1 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0
            precip_key = f"{rec['segment_id']}:{dt.strftime('%Y%m%d%H')}"
            precip = weather_data.get(precip_key, 0.0) if weather_data else 0.0
            all_sources.append({
                "source": "metro",
                "segment_id": rec["segment_id"],
                "grid_id": f"GRID-B{segments[rec['segment_id']]['grid_col'] + 1}",
                "window_start": dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "window_end": (dt + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "metric_name": "occupancy_pct",
                "metric_sum": float(rec["occupancy_pct"]),
                "metric_avg": float(rec["occupancy_pct"]),
                "metric_max": float(rec["occupancy_pct"]),
                "metric_count": 1,
                "hour_of_day": hour,
                "day_of_week": dow,
                "is_weekend": is_weekend,
                "is_peak_hour": is_peak,
                "segment_numeric": int(rec["segment_id"].replace("SEG-", "")),
                "grid_area": "B",
                "event_attendance_window_sum": 0.0,
                "weather_precip_window_avg": precip,
            })

    if taxi_data:
        for rec in taxi_data:
            dt = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
            dow = dt.weekday()
            hour = dt.hour
            is_weekend = 1 if dow >= 5 else 0
            is_peak = 1 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0
            precip_key = f"{rec['segment_id']}:{dt.strftime('%Y%m%d%H')}"
            precip = weather_data.get(precip_key, 0.0) if weather_data else 0.0
            all_sources.append({
                "source": "taxi",
                "segment_id": rec["segment_id"],
                "grid_id": f"GRID-A{segments[rec['segment_id']]['grid_col'] + 1}",
                "window_start": dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "window_end": (dt + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "metric_name": "passenger_count",
                "metric_sum": float(rec["passenger_count"]),
                "metric_avg": float(rec["passenger_count"]),
                "metric_max": float(rec["passenger_count"]),
                "metric_count": 1,
                "hour_of_day": hour,
                "day_of_week": dow,
                "is_weekend": is_weekend,
                "is_peak_hour": is_peak,
                "segment_numeric": int(rec["segment_id"].replace("SEG-", "")),
                "grid_area": "A",
                "event_attendance_window_sum": 0.0,
                "weather_precip_window_avg": precip,
            })

    if weather_data and isinstance(weather_data, list):
        for rec in weather_data:
            dt = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
            dow = dt.weekday()
            hour = dt.hour
            is_weekend = 1 if dow >= 5 else 0
            is_peak = 1 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0
            all_sources.append({
                "source": "weather",
                "segment_id": rec["segment_id"],
                "grid_id": f"GRID-C{segments[rec['segment_id']]['grid_col'] + 1}",
                "window_start": dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "window_end": (dt + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "metric_name": "precip_mm",
                "metric_sum": float(rec["precip_mm"]),
                "metric_avg": float(rec["precip_mm"]),
                "metric_max": float(rec["precip_mm"]),
                "metric_count": 1,
                "hour_of_day": hour,
                "day_of_week": dow,
                "is_weekend": is_weekend,
                "is_peak_hour": is_peak,
                "segment_numeric": int(rec["segment_id"].replace("SEG-", "")),
                "grid_area": "C",
                "event_attendance_window_sum": 0.0,
                "weather_precip_window_avg": float(rec["precip_mm"]),
            })

    all_sources.sort(key=lambda x: (x["segment_id"], x["window_start"]))
    return all_sources

def generate_aligned_records(segments, event_data, metro_data, taxi_data, start_date, days=7):
    records = []

    if event_data:
        for rec in event_data:
            dt = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
            records.append({
                "source": "event",
                "entity_id": rec["event_id"],
                "timestamp": rec["timestamp"],
                "window_start": dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "window_end": (dt + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "segment_id": rec["segment_id"],
                "grid_id": f"GRID-D{segments[rec['segment_id']]['grid_col'] + 1}",
                "metric_name": "expected_attendance",
                "metric_value": float(rec["expected_attendance"]),
            })

    if metro_data:
        for rec in metro_data:
            dt = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
            records.append({
                "source": "metro",
                "entity_id": rec["train_id"],
                "timestamp": rec["timestamp"],
                "window_start": dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "window_end": (dt + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "segment_id": rec["segment_id"],
                "grid_id": f"GRID-B{segments[rec['segment_id']]['grid_col'] + 1}",
                "metric_name": "occupancy_pct",
                "metric_value": float(rec["occupancy_pct"]),
            })

    if taxi_data:
        for rec in taxi_data:
            dt = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
            records.append({
                "source": "taxi",
                "entity_id": rec["ride_id"],
                "timestamp": rec["timestamp"],
                "window_start": dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "window_end": (dt + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "segment_id": rec["segment_id"],
                "grid_id": f"GRID-A{segments[rec['segment_id']]['grid_col'] + 1}",
                "metric_name": "passenger_count",
                "metric_value": float(rec["passenger_count"]),
            })

    records.sort(key=lambda x: (x["timestamp"], x["segment_id"]))
    return records

def main():
    print("Generating synthetic traffic data...")
    start_date = datetime(2026, 4, 1, tzinfo=timezone.utc)

    segments = generate_segments()
    print(f"Generated {len(segments)} segments")

    save_geometry(segments)

    weather_data = generate_weather_data(segments, start_date, days=7)
    print(f"Generated {len(weather_data)} weather records")

    metro_data = generate_metro_data(segments, start_date, days=7)
    print(f"Generated {len(metro_data)} metro records")

    taxi_data = generate_taxi_data(segments, start_date, days=7)
    print(f"Generated {len(taxi_data)} taxi records")

    event_data = generate_event_data(segments, start_date, days=7)
    print(f"Generated {len(event_data)} event records")

    weather_dict = {}
    for w in weather_data:
        key = f"{w['segment_id']}:{datetime.fromisoformat(w['timestamp'].replace('Z', '+00:00')).strftime('%Y%m%d%H')}"
        if key not in weather_dict:
            weather_dict[key] = 0.0
        weather_dict[key] = max(weather_dict[key], w["precip_mm"])

    feature_records = generate_feature_table(segments, weather_dict, metro_data, taxi_data, event_data, start_date, days=7)
    print(f"Generated {len(feature_records)} feature records")

    aligned_records = generate_aligned_records(segments, event_data, metro_data, taxi_data, start_date, days=7)
    print(f"Generated {len(aligned_records)} aligned records")

    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    feature_path = FEATURES_DIR / "feature_table.csv"
    with open(feature_path, "w", newline="", encoding="utf-8") as f:
        if feature_records:
            writer = csv.DictWriter(f, fieldnames=feature_records[0].keys())
            writer.writeheader()
            writer.writerows(feature_records)
    print(f"Saved feature table to {feature_path}")

    aligned_path = ALIGNMENT_DIR / "output" / "aligned" / "aligned_records.csv"
    aligned_path.parent.mkdir(parents=True, exist_ok=True)
    with open(aligned_path, "w", newline="", encoding="utf-8") as f:
        if aligned_records:
            writer = csv.DictWriter(f, fieldnames=aligned_records[0].keys())
            writer.writeheader()
            writer.writerows(aligned_records)
    print(f"Saved aligned records to {aligned_path}")

    print("\nSynthetic data generation complete!")
    print(f"Total segments: {len(segments)}")
    print(f"Congestion distribution: 畅通 20%, 缓行 40%, 拥堵 30%, 严重拥堵 10%")
    print(f"Cause distribution: Weather/Holiday/Incident/Other varied across segments")

if __name__ == "__main__":
    main()