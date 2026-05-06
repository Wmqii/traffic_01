import { APP_CONFIG } from "./config.js";
import { TrafficApi } from "./api.js";

function colorByHeat(score) {
  if (score >= 0.85) return "#c1121f";
  if (score >= 0.65) return "#e36414";
  if (score >= 0.45) return "#f4a261";
  return "#2a9d8f";
}

export class MapManager {
  constructor() {
    this.map = L.map("map").setView(APP_CONFIG.mapCenter, APP_CONFIG.mapZoom);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap",
    }).addTo(this.map);

    this.heatLayer = null;
    this.eventLayer = L.layerGroup().addTo(this.map);
    this.segmentLayer = L.layerGroup().addTo(this.map);

    this.layerControl = L.control.layers({}, {
      "事件点": this.eventLayer,
      "路段线": this.segmentLayer,
    }).addTo(this.map);

    this.api = new TrafficApi();
    this.segmentCoords = {};
  }

  async loadSegmentCoords() {
    try {
      const geometries = await this.api.getSegmentGeometries();
      if (geometries && geometries.length > 0) {
        const newCoords = {};
        geometries.forEach(geom => {
          if (geom.segment_id && geom.coordinates && geom.coordinates.length >= 2) {
            newCoords[geom.segment_id] = geom.coordinates;
          }
        });
        if (Object.keys(newCoords).length > 0) {
          this.segmentCoords = newCoords;
          console.log(`Loaded ${Object.keys(newCoords).length} segments from API`);
        }
      }
    } catch (error) {
      console.warn("Failed to load segment geometries from API, using fallback:", error);
    }
  }

  getCoords(segmentId) {
    return this.segmentCoords[segmentId] || null;
  }

  renderHeat(heatLayerData) {
    const points = [];
    (heatLayerData.segments || []).forEach((segment) => {
      const line = this.getCoords(segment.segment_id);
      if (!line) return;
      const midpoint = [
        (line[0][0] + line[1][0]) / 2,
        (line[0][1] + line[1][1]) / 2,
        Math.max(0.2, Number(segment.heat_score) || 0.2),
      ];
      points.push(midpoint);
    });

    if (this.heatLayer) {
      this.map.removeLayer(this.heatLayer);
    }
    this.heatLayer = L.heatLayer(points, { radius: 25, blur: 20, maxZoom: 15 });
    this.heatLayer.addTo(this.map);
  }

  renderEvents(events) {
    this.eventLayer.clearLayers();
    (events || []).forEach((event) => {
      const line = this.getCoords(event.segment_id);
      if (!line) return;
      const latlng = [(line[0][0] + line[1][0]) / 2, (line[0][1] + line[1][1]) / 2];
      const marker = L.circleMarker(latlng, {
        radius: 6,
        color: "#d62828",
        fillColor: "#f77f00",
        fillOpacity: 0.75,
      });
      marker.bindPopup(`${event.name}<br/>${event.segment_id}<br/>${event.severity}`);
      marker.addTo(this.eventLayer);
    });
  }

  renderSegments(heatLayerData) {
    this.segmentLayer.clearLayers();
    const scoreMap = new Map((heatLayerData.segments || []).map((item) => [item.segment_id, item.heat_score]));

    Object.entries(this.segmentCoords).forEach(([segmentId, coords]) => {
      const score = scoreMap.get(segmentId) || 0;
      const line = L.polyline(coords, {
        color: colorByHeat(score),
        weight: 5,
        opacity: 0.85,
      });
      line.bindTooltip(`${segmentId} | heat: ${Number(score).toFixed(2)}`);
      line.addTo(this.segmentLayer);
    });
  }
}