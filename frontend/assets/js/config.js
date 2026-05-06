export const APP_CONFIG = {
  apiBaseUrl: (() => { const saved = localStorage.getItem("traffic_api_base"); if (saved && saved.includes(":8000")) { return "http://127.0.0.1:8005"; } return saved || "http://127.0.0.1:8005"; })(),
  fallbackMode: true,
  mapCenter: [31.220, 121.475],
  mapZoom: 12,
};
