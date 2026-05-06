import { APP_CONFIG } from "./config.js";

function parseJsonSafe(text) {
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

export class TrafficApi {
  constructor() {
    this.baseUrl = APP_CONFIG.apiBaseUrl;
    this.token = localStorage.getItem("traffic_token") || "";
  }

  setToken(token) {
    this.token = token || "";
    if (token) {
      localStorage.setItem("traffic_token", token);
    } else {
      localStorage.removeItem("traffic_token");
    }
  }

  async request(path, { method = "GET", body, auth = true } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth && this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    const text = await response.text();
    const payload = text ? parseJsonSafe(text) : {};
    if (!response.ok) {
      const message = payload.detail || payload.raw || `HTTP ${response.status}`;
      throw new Error(message);
    }
    return payload;
  }

  login(username, password) {
    return this.request("/api/v1/auth/login", {
      method: "POST",
      body: { username, password },
      auth: false,
    });
  }

  me() {
    return this.request("/api/v1/auth/me");
  }

  getHeatLayer() {
    return this.request("/api/v1/map/layers/heat");
  }

  getEvents() {
    return this.request("/api/v1/congestion/events");
  }

  getPrediction(segmentId) {
    return this.request(`/api/v1/predictions/segments/${segmentId}`);
  }

  getAttribution(eventId) {
    return this.request(`/api/v1/attributions/events/${eventId}`);
  }

  getSegmentGeometries() {
    return this.request("/api/v1/map/segments/geometry");
  }

  getAudit() {
    return this.request("/api/v1/admin/audit");
  }
}
