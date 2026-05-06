import { APP_CONFIG } from "./config.js";
import { mockData } from "./mock.js";
import { TrafficApi } from "./api.js";
import { ChartManager } from "./charts.js";
import { MapManager } from "./map.js";

const api = new TrafficApi();
const charts = new ChartManager();
const map = new MapManager();

const state = {
  mode: "mock",
  user: null,
  events: [],
  heatLayer: null,
  prediction: null,
  attribution: null,
};

function $(id) {
  return document.getElementById(id);
}

function writeJson(id, data) {
  $(id).textContent = JSON.stringify(data, null, 2);
}

function setStatus(text) {
  $("status-text").textContent = `状态：${text}`;
}

function setModeIndicator(text) {
  $("mode-indicator").textContent = text;
}

function renderKpiCards() {
  const grid = $("kpi-grid");
  const cards = [
    { title: "事件数量", value: state.events.length },
    { title: "平均热度", value: (state.heatLayer?.segments?.reduce((n, i) => n + Number(i.heat_score || 0), 0) / Math.max(state.heatLayer?.segments?.length || 1, 1)).toFixed(2) },
    { title: "预测等级", value: state.prediction?.predicted_congestion || "N/A" },
    { title: "置信度", value: state.prediction ? `${Math.round(Number(state.prediction.confidence || 0) * 100)}%` : "N/A" },
  ];

  grid.innerHTML = cards
    .map((card) => `<article class="kpi"><h4>${card.title}</h4><strong>${card.value}</strong></article>`)
    .join("");
}

function renderEventList() {
  const list = $("event-list");
  list.innerHTML = "";
  state.events.forEach((event) => {
    const button = document.createElement("button");
    button.textContent = `${event.name} | ${event.segment_id} | ${event.severity}`;
    button.addEventListener("click", async () => {
      await loadAttribution(event.event_id);
    });
    const li = document.createElement("li");
    li.appendChild(button);
    list.appendChild(li);
  });
}

function applyTabBehavior() {
  const buttons = document.querySelectorAll(".nav-btn");
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      buttons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      const tabName = button.dataset.tab;
      document.querySelectorAll(".tab-panel").forEach((panel) => {
        panel.classList.toggle("active", panel.id === `tab-${tabName}`);
      });
      if (tabName === "realtime") {
        setTimeout(() => map.map.invalidateSize(), 120);
      }
    });
  });
}

async function withFallback(fn, fallbackProvider) {
  try {
    const data = await fn();
    state.mode = "api";
    setModeIndicator(`当前数据模式：API Online (${APP_CONFIG.apiBaseUrl})`);
    return data;
  } catch {
    state.mode = "mock";
    setModeIndicator("当前数据模式：Mock Fallback");
    return fallbackProvider();
  }
}

async function login(username, password) {
  try {
    const payload = await api.login(username, password);
    api.setToken(payload.access_token);
    setStatus(`登录成功(${payload.role})`);
    const profile = await withFallback(() => api.me(), () => mockData.user);
    state.user = profile;
    writeJson("user-profile", profile);
  } catch (error) {
    setStatus(`登录失败: ${error.message}`);
    api.setToken("");
    state.user = mockData.user;
    writeJson("user-profile", state.user);
  }
}

async function loadAttribution(eventId) {
  state.attribution = await withFallback(() => api.getAttribution(eventId), () => mockData.attribution);
  writeJson("attribution-detail", state.attribution);
  charts.renderRadar(state.attribution);
}

async function refreshAll() {
  setStatus("加载中...");
  const segmentId = $("segment-select").value;

  state.heatLayer = await withFallback(() => api.getHeatLayer(), () => mockData.heatLayer);
  state.events = await withFallback(() => api.getEvents(), () => mockData.events);
  state.prediction = await withFallback(() => api.getPrediction(segmentId), () => ({ ...mockData.prediction, segment_id: segmentId }));
  state.attribution = await withFallback(
    () => api.getAttribution((state.events[0] && state.events[0].event_id) || "event-bridge"),
    () => mockData.attribution,
  );
  const audit = await withFallback(() => api.getAudit(), () => ({ error: "当前账号无 admin 权限", fallback: mockData.audit }));

  renderKpiCards();
  renderEventList();
  map.renderHeat(state.heatLayer);
  map.renderEvents(state.events);
  map.renderSegments(state.heatLayer);

  charts.renderTrend(state.heatLayer);
  charts.renderRadar(state.attribution);
  charts.renderFunnel(state.events);
  charts.renderSankey(state.prediction);

  writeJson("prediction-detail", state.prediction);
  writeJson("attribution-detail", state.attribution);
  writeJson("audit-snapshot", audit);
  if (!state.user) {
    state.user = await withFallback(() => api.me(), () => mockData.user);
  }
  writeJson("user-profile", state.user);

  setStatus(`完成 (${new Date().toLocaleString("zh-CN")}, ${state.mode.toUpperCase()})`);
}

function bindEvents() {
  $("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await login($("username").value.trim(), $("password").value.trim());
    await refreshAll();
  });

  $("refresh-btn").addEventListener("click", async () => {
    await refreshAll();
  });
}

async function bootstrap() {
  applyTabBehavior();
  bindEvents();
  await map.loadSegmentCoords();
  await login($("username").value, $("password").value);
  await refreshAll();
}

bootstrap();
