-- Core schema DDL for traffic congestion system (M2 addendum)

CREATE TABLE IF NOT EXISTS dim_region (
  region_id VARCHAR(32) PRIMARY KEY,
  region_name VARCHAR(128) NOT NULL,
  city_code VARCHAR(16) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_grid (
  grid_id VARCHAR(32) PRIMARY KEY,
  region_id VARCHAR(32) NOT NULL,
  grid_area VARCHAR(16) NOT NULL,
  center_lng DOUBLE PRECISION,
  center_lat DOUBLE PRECISION,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_grid_region FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
);

CREATE TABLE IF NOT EXISTS dim_segment (
  segment_id VARCHAR(32) PRIMARY KEY,
  grid_id VARCHAR(32) NOT NULL,
  road_name VARCHAR(128),
  direction VARCHAR(16),
  segment_numeric INTEGER,
  geometry_wkt TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_segment_grid FOREIGN KEY (grid_id) REFERENCES dim_grid(grid_id)
);

CREATE TABLE IF NOT EXISTS fact_traffic_metric_15m (
  fact_id BIGSERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL,
  segment_id VARCHAR(32) NOT NULL,
  metric_name VARCHAR(64) NOT NULL,
  metric_value DOUBLE PRECISION NOT NULL,
  window_start TIMESTAMP NOT NULL,
  window_end TIMESTAMP NOT NULL,
  ingest_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  quality_score DOUBLE PRECISION,
  CONSTRAINT fk_fact_segment FOREIGN KEY (segment_id) REFERENCES dim_segment(segment_id)
) PARTITION BY RANGE (window_start);

CREATE TABLE IF NOT EXISTS fact_congestion_event (
  event_id VARCHAR(64) PRIMARY KEY,
  segment_id VARCHAR(32) NOT NULL,
  event_type VARCHAR(64) NOT NULL,
  severity VARCHAR(16) NOT NULL,
  expected_attendance DOUBLE PRECISION,
  start_ts TIMESTAMP NOT NULL,
  end_ts TIMESTAMP NOT NULL,
  source VARCHAR(32) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_event_segment FOREIGN KEY (segment_id) REFERENCES dim_segment(segment_id)
) PARTITION BY RANGE (start_ts);

CREATE TABLE IF NOT EXISTS model_prediction_15m (
  prediction_id BIGSERIAL PRIMARY KEY,
  model_version VARCHAR(64) NOT NULL,
  model_type VARCHAR(32) NOT NULL,
  segment_id VARCHAR(32) NOT NULL,
  window_start TIMESTAMP NOT NULL,
  window_end TIMESTAMP NOT NULL,
  predicted_value DOUBLE PRECISION NOT NULL,
  confidence DOUBLE PRECISION,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_prediction_segment FOREIGN KEY (segment_id) REFERENCES dim_segment(segment_id)
) PARTITION BY RANGE (window_start);

CREATE TABLE IF NOT EXISTS model_attribution (
  attribution_id BIGSERIAL PRIMARY KEY,
  prediction_id BIGINT NOT NULL,
  feature_name VARCHAR(128) NOT NULL,
  contribution DOUBLE PRECISION NOT NULL,
  explanation_type VARCHAR(32) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_attr_prediction FOREIGN KEY (prediction_id) REFERENCES model_prediction_15m(prediction_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_metric_window_segment
  ON fact_traffic_metric_15m (window_start, segment_id, metric_name);

CREATE INDEX IF NOT EXISTS idx_event_time_segment
  ON fact_congestion_event (start_ts, segment_id, severity);

CREATE INDEX IF NOT EXISTS idx_prediction_window_segment
  ON model_prediction_15m (window_start, segment_id, model_version);

CREATE INDEX IF NOT EXISTS idx_attr_prediction
  ON model_attribution (prediction_id, feature_name);
