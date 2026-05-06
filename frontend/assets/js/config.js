export const APP_CONFIG = {
  apiBaseUrl: localStorage.getItem("traffic_api_base") || "http://127.0.0.1:8005",
  fallbackMode: true,
  mapCenter: [31.220, 121.475],
  mapZoom: 12,
};
