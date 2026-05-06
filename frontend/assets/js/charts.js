function withBase(optionTitle) {
  return {
    backgroundColor: "transparent",
    textStyle: { fontFamily: "Noto Sans SC" },
    title: {
      text: optionTitle,
      left: 10,
      top: 4,
      textStyle: { fontSize: 12, fontWeight: 500, color: "#5b6870" },
    },
    tooltip: { trigger: "item" },
  };
}

export class ChartManager {
  constructor() {
    this.charts = {
      trend: echarts.init(document.getElementById("trend-chart")),
      radar: echarts.init(document.getElementById("radar-chart")),
      funnel: echarts.init(document.getElementById("funnel-chart")),
      sankey: echarts.init(document.getElementById("sankey-chart")),
    };
    window.addEventListener("resize", () => {
      Object.values(this.charts).forEach((chart) => chart.resize());
    });
  }

  renderTrend(heatLayer) {
    const series = heatLayer.segments.slice(0, 6).map((item, idx) => ({
      name: item.segment_id,
      value: Math.round((item.heat_score + idx * 0.03) * 100),
    }));
    const option = {
      ...withBase("未来 6 个时间片拥堵指数"),
      xAxis: {
        type: "category",
        data: ["T+15", "T+30", "T+45", "T+60", "T+75", "T+90"],
      },
      yAxis: { type: "value", max: 100 },
      series: [{
        type: "line",
        smooth: true,
        areaStyle: {},
        itemStyle: { color: "#0e7c86" },
        data: series.map((s) => s.value),
      }],
    };
    this.charts.trend.setOption(option, true);
  }

  renderRadar(attribution) {
    const drivers = attribution.drivers?.slice(0, 5) || [];
    const indicators = drivers.map((driver) => ({ name: driver.name, max: 1 }));
    const option = {
      ...withBase("归因驱动雷达"),
      radar: { indicator: indicators.length ? indicators : [{ name: "N/A", max: 1 }] },
      series: [{
        type: "radar",
        areaStyle: { opacity: 0.25 },
        data: [{
          value: drivers.length ? drivers.map((driver) => Number(driver.impact) || 0) : [0],
          name: attribution.event_id || "N/A",
        }],
      }],
    };
    this.charts.radar.setOption(option, true);
  }

  renderFunnel(events) {
    const levelCount = events.reduce((acc, item) => {
      acc[item.severity] = (acc[item.severity] || 0) + 1;
      return acc;
    }, {});
    const data = Object.entries(levelCount).map(([name, value]) => ({ name, value }));
    const option = {
      ...withBase("事件严重度漏斗"),
      series: [{
        type: "funnel",
        left: "10%",
        width: "80%",
        minSize: "30%",
        maxSize: "95%",
        label: { show: true, position: "inside" },
        data: data.length ? data : [{ name: "无数据", value: 1 }],
      }],
    };
    this.charts.funnel.setOption(option, true);
  }

  renderSankey(prediction) {
    const nodes = [{ name: prediction.segment_id || "segment" }];
    const links = [];
    (prediction.feature_summary || []).slice(0, 6).forEach((item) => {
      const source = `${item.source}:${item.metric_name}`;
      nodes.push({ name: source });
      links.push({ source, target: prediction.segment_id || "segment", value: Number(item.metric_value) || 1 });
    });
    const option = {
      ...withBase("特征源-路段影响流"),
      series: [{
        type: "sankey",
        data: nodes,
        links,
        emphasis: { focus: "adjacency" },
        lineStyle: { color: "gradient", curveness: 0.4 },
      }],
    };
    this.charts.sankey.setOption(option, true);
  }
}
