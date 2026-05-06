const now = new Date();

export const mockData = {
  user: {
    username: "viewer",
    role: "viewer",
    display_name: "Read-Only Viewer",
  },
  heatLayer: {
    layer_id: "heat-layer-mock",
    generated_at: now.toISOString(),
    segments: [
      { segment_id: "SEG-1001", grid_id: "GRID-A", heat_score: 0.91, updated_at: now.toISOString() },
      { segment_id: "SEG-1002", grid_id: "GRID-B", heat_score: 0.62, updated_at: now.toISOString() },
      { segment_id: "SEG-2001", grid_id: "GRID-C", heat_score: 0.73, updated_at: now.toISOString() },
      { segment_id: "SEG-3001", grid_id: "GRID-D", heat_score: 0.48, updated_at: now.toISOString() }
    ],
  },
  events: [
    { event_id: "event-bridge", segment_id: "SEG-4001", name: "Event Bridge", grid_id: "GRID-B", severity: "High", confidence: 0.88, window_start: now.toISOString(), window_end: now.toISOString() },
    { event_id: "event-market", segment_id: "SEG-1003", name: "Event Market", grid_id: "GRID-C", severity: "Moderate", confidence: 0.74, window_start: now.toISOString(), window_end: now.toISOString() }
  ],
  prediction: {
    segment_id: "SEG-1001",
    source: "taxi",
    window_start: now.toISOString(),
    window_end: now.toISOString(),
    predicted_congestion: "High",
    confidence: 0.86,
    feature_summary: [
      { metric_name: "trip_count", metric_value: 1980, source: "taxi" },
      { metric_name: "occupancy_pct", metric_value: 69, source: "metro" },
      { metric_name: "precip_mm", metric_value: 18, source: "weather" }
    ]
  },
  attribution: {
    event_id: "event-bridge",
    segment_id: "SEG-4001",
    generated_at: now.toISOString(),
    predicted_severity: "High",
    drivers: [
      { name: "expected_attendance", source: "event", value: 12000, impact: 0.95, notes: "Window T-15m" },
      { name: "trip_count", source: "taxi", value: 1800, impact: 0.82, notes: "Window T-15m" },
      { name: "occupancy_pct", source: "metro", value: 66, impact: 0.71, notes: "Window T-15m" }
    ]
  },
  audit: {
    generated_at: now.toISOString(),
    user_count: 3,
    endpoint_count: 7,
  },
};
