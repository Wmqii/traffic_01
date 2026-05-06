(function () {
  const state = {
    apiBase: (() => { const saved = localStorage.getItem('traffic_api_base'); if (saved && saved.includes(':8000')) { return 'http://127.0.0.1:8005'; } return saved || 'http://127.0.0.1:8005'; })(),
    windowMinutes: 15,
    selectedSegmentId: '',
    overview: [],
    trend: null,
    causes: null,
    predictionAnalysis: null,
    segmentPredictionSnapshots: [],
    modelErrors: [],
    segmentReport: null,
    currentPrediction: null,
    heatLayer: null,
    events: [],
    segmentGeometry: null,
    segmentGeometryMeta: null,
    map: null,
    mapFitted: false,
    baseTileLayer: null,
    mapProviderName: '',
    predictionMap: null,
    predictionMapFitted: false,
    predictionBaseTileLayer: null,
    predictionMapProviderName: '',
    charts: {},
    mapLayers: {
      heat: null,
      events: null,
      segments: null,
    },
    predictionMapLayers: {
      segments: null,
    },
    homeMap: null,
    homeMapFitted: false,
    homeBaseTileLayer: null,
    homeMapProviderName: '',
    homeMapLayers: {
      segments: null,
    },
    predictionPlayback: {
      timer: null,
      frameIndex: 0,
    },
    mapRefs: {
      segmentLines: {},
      predictionSegmentLines: {},
      homeSegmentLines: {},
      heatMarkers: {},
      eventMarkers: {},
    },
    useFallback: false,
    isRefreshing: false,
    isSwitchingSegment: false,
    lastRefreshAt: '',
    autoToPrediction: localStorage.getItem('traffic_auto_to_prediction') !== '0',
    segmentSearchKeyword: '',
    comparisonSegmentIds: [],
    comparisonPredictions: {},
    isLoadingComparison: false,
  };

  const segmentGeometry = {
    'SEG-1001': [[31.200279, 121.43905], [31.202829, 121.442496]],
    'SEG-1002': [[31.200473, 121.448353], [31.204257, 121.451527]],
    'SEG-1003': [[31.199844, 121.45506], [31.202281, 121.45907]],
    'SEG-1004': [[31.199053, 121.463398], [31.202353, 121.467488]],
    'SEG-1005': [[31.199441, 121.472179], [31.20306, 121.475192]],
    'SEG-1006': [[31.200612, 121.480396], [31.203292, 121.483707]],
    'SEG-1007': [[31.200914, 121.487673], [31.2031, 121.490867]],
    'SEG-1008': [[31.200695, 121.496207], [31.204309, 121.500667]],
    'SEG-1009': [[31.200072, 121.504946], [31.20283, 121.50905]],
    'SEG-1010': [[31.200659, 121.512237], [31.204382, 121.516392]],
    'SEG-1011': [[31.206409, 121.439092], [31.208865, 121.44267]],
    'SEG-1012': [[31.20516, 121.447466], [31.207362, 121.451022]],
    'SEG-1013': [[31.206271, 121.45573], [31.209012, 121.459149]],
    'SEG-1014': [[31.205534, 121.464873], [31.20883, 121.469092]],
    'SEG-1015': [[31.205342, 121.472458], [31.207669, 121.476217]],
    'SEG-1016': [[31.206979, 121.48028], [31.210093, 121.484649]],
    'SEG-1017': [[31.206686, 121.488552], [31.209144, 121.491616]],
    'SEG-1018': [[31.205631, 121.495535], [31.208053, 121.500421]],
    'SEG-1019': [[31.206753, 121.503629], [31.210064, 121.507421]],
    'SEG-1020': [[31.206829, 121.511918], [31.209359, 121.515411]],
    'SEG-1021': [[31.212123, 121.439525], [31.215292, 121.444321]],
    'SEG-1022': [[31.211799, 121.447439], [31.215794, 121.451458]],
    'SEG-1023': [[31.211182, 121.455094], [31.213401, 121.459349]],
    'SEG-1024': [[31.212584, 121.463844], [31.214711, 121.467608]],
    'SEG-1025': [[31.212992, 121.472058], [31.216934, 121.47678]],
    'SEG-1026': [[31.211023, 121.480441], [31.214386, 121.484515]],
    'SEG-1027': [[31.211534, 121.488282], [31.213757, 121.492151]],
    'SEG-1028': [[31.211907, 121.496908], [31.215659, 121.500434]],
    'SEG-1029': [[31.212001, 121.503357], [31.215826, 121.508098]],
    'SEG-1030': [[31.211597, 121.512278], [31.214815, 121.515584]],
    'SEG-1031': [[31.218525, 121.440079], [31.222082, 121.444139]],
    'SEG-1032': [[31.217001, 121.447648], [31.21904, 121.452507]],
    'SEG-1033': [[31.218757, 121.456663], [31.221372, 121.459779]],
    'SEG-1034': [[31.218756, 121.464894], [31.220927, 121.468866]],
    'SEG-1035': [[31.217138, 121.472521], [31.22067, 121.475778]],
    'SEG-1036': [[31.217951, 121.4801], [31.220481, 121.484844]],
    'SEG-1037': [[31.217846, 121.487424], [31.220925, 121.491883]],
    'SEG-1038': [[31.217402, 121.495623], [31.221393, 121.499923]],
    'SEG-1039': [[31.217876, 121.504035], [31.220118, 121.507485]],
    'SEG-1040': [[31.217676, 121.512177], [31.220136, 121.515617]],
    'SEG-1041': [[31.223142, 121.440262], [31.2256, 121.445073]],
    'SEG-1042': [[31.224719, 121.447142], [31.227195, 121.45148]],
    'SEG-1043': [[31.223428, 121.455265], [31.2273, 121.459407]],
    'SEG-1044': [[31.223945, 121.464569], [31.22756, 121.46795]],
    'SEG-1045': [[31.223194, 121.471862], [31.226041, 121.475796]],
    'SEG-1046': [[31.224458, 121.480347], [31.228426, 121.483544]],
    'SEG-1047': [[31.223805, 121.487679], [31.227529, 121.491176]],
    'SEG-1048': [[31.22338, 121.495897], [31.226224, 121.499454]],
    'SEG-1049': [[31.2235, 121.504847], [31.226386, 121.509569]],
    'SEG-1050': [[31.224101, 121.511101], [31.228099, 121.515773]],
    'SEG-1051': [[31.230938, 121.440853], [31.234635, 121.444185]],
    'SEG-1052': [[31.229971, 121.447427], [31.232773, 121.450545]],
    'SEG-1053': [[31.229758, 121.456971], [31.232288, 121.461539]],
    'SEG-1054': [[31.22991, 121.463846], [31.233825, 121.468837]],
    'SEG-1055': [[31.230112, 121.472437], [31.232421, 121.47603]],
    'SEG-1056': [[31.230937, 121.480158], [31.234022, 121.484654]],
    'SEG-1057': [[31.229114, 121.488168], [31.23212, 121.492874]],
    'SEG-1058': [[31.229315, 121.496922], [31.231475, 121.500293]],
    'SEG-1059': [[31.23019, 121.50435], [31.23266, 121.50759]],
    'SEG-1060': [[31.230781, 121.511492], [31.23397, 121.515731]],
    'SEG-1061': [[31.235838, 121.440167], [31.238884, 121.445037]],
    'SEG-1062': [[31.235409, 121.448432], [31.237886, 121.452224]],
    'SEG-1063': [[31.236343, 121.4556], [31.238976, 121.460104]],
    'SEG-1064': [[31.235145, 121.463917], [31.239142, 121.468909]],
    'SEG-1065': [[31.235147, 121.471426], [31.237677, 121.476293]],
    'SEG-1066': [[31.236762, 121.480759], [31.239501, 121.484074]],
    'SEG-1067': [[31.236667, 121.488407], [31.239891, 121.493382]],
    'SEG-1068': [[31.236308, 121.495016], [31.239942, 121.498614]],
    'SEG-1069': [[31.236327, 121.504878], [31.238595, 121.508109]],
    'SEG-1070': [[31.235214, 121.512106], [31.237759, 121.516316]],
    'SEG-1071': [[31.242435, 121.439407], [31.245704, 121.442935]],
    'SEG-1072': [[31.241977, 121.448811], [31.245669, 121.451995]],
    'SEG-1073': [[31.241847, 121.455553], [31.243854, 121.460096]],
    'SEG-1074': [[31.242274, 121.463524], [31.245757, 121.467627]],
    'SEG-1075': [[31.241855, 121.471019], [31.244006, 121.475786]],
    'SEG-1076': [[31.242808, 121.480091], [31.246477, 121.484256]],
    'SEG-1077': [[31.241296, 121.487255], [31.243913, 121.492053]],
    'SEG-1078': [[31.242592, 121.496721], [31.24639, 121.500142]],
    'SEG-1079': [[31.241499, 121.503206], [31.245059, 121.507974]],
    'SEG-1080': [[31.241813, 121.512241], [31.244122, 121.517101]],
    'SEG-1081': [[31.248729, 121.440952], [31.252351, 121.445715]],
    'SEG-1082': [[31.24705, 121.448473], [31.249714, 121.453335]],
    'SEG-1083': [[31.248604, 121.456728], [31.252226, 121.460262]],
    'SEG-1084': [[31.248575, 121.463216], [31.252319, 121.467933]],
    'SEG-1085': [[31.247445, 121.472633], [31.250365, 121.476244]],
    'SEG-1086': [[31.248591, 121.479455], [31.250638, 121.482841]],
    'SEG-1087': [[31.247657, 121.488729], [31.25159, 121.492287]],
    'SEG-1088': [[31.248283, 121.495799], [31.252245, 121.499872]],
    'SEG-1089': [[31.248878, 121.503231], [31.252819, 121.506588]],
    'SEG-1090': [[31.248925, 121.511531], [31.251142, 121.5154]],
    'SEG-1091': [[31.254457, 121.439627], [31.25767, 121.44365]],
    'SEG-1092': [[31.25377, 121.448153], [31.25628, 121.452571]],
    'SEG-1093': [[31.253003, 121.456851], [31.25608, 121.46129]],
    'SEG-1094': [[31.254484, 121.464341], [31.257212, 121.467481]],
    'SEG-1095': [[31.254328, 121.47166], [31.256956, 121.476356]],
    'SEG-1096': [[31.25444, 121.479601], [31.257058, 121.483417]],
    'SEG-1097': [[31.253805, 121.487591], [31.256059, 121.491432]],
    'SEG-1098': [[31.254881, 121.496355], [31.258686, 121.500586]],
    'SEG-1099': [[31.253602, 121.504096], [31.255603, 121.50767]],
    'SEG-1100': [[31.25386, 121.51216], [31.257169, 121.51609]],
    'SEG-1101': [[31.259884, 121.439427], [31.262831, 121.44423]],
  };

  const gridCenters = {
    'GRID-A1': [31.227, 121.463],
    'GRID-A2': [31.225, 121.478],
    'GRID-A3': [31.219, 121.451],
    'GRID-B1': [31.236, 121.454],
    'GRID-B2': [31.236, 121.471],
    'GRID-B3': [31.233, 121.441],
    'GRID-C1': [31.215, 121.466],
    'GRID-C2': [31.212, 121.482],
    'GRID-C3': [31.208, 121.454],
    'GRID-D1': [31.246, 121.467],
    'GRID-D2': [31.248, 121.483],
    'GRID-D3': [31.244, 121.447],
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function hasEcharts() {
    return typeof window.echarts !== 'undefined';
  }

  function hasLeaflet() {
    return typeof window.L !== 'undefined';
  }

  function getSegmentGeometryMap() {
    return state.segmentGeometry || segmentGeometry;
  }

  function setStatus(text) {
    byId('dataStatus').textContent = text;
  }

  function geometrySourceLabel() {
    const source = state.segmentGeometryMeta && state.segmentGeometryMeta.source;
    if (source === 'file') return '真实路网文件';
    if (source === 'fallback') return '演示路网(回退)';
    return '未知';
  }

  function selectedPredictionSummaryText() {
    const row = (state.segmentPredictionSnapshots || []).find((item) => item.segment_id === state.selectedSegmentId);
    if (!row) return '预测结论=暂无';
    return `预测结论=${row.pred_congestion_level}(${row.pred_congestion_index})`;
  }

  function getSegmentSnapshot(segmentId) {
    return (state.segmentPredictionSnapshots || []).find((item) => item.segment_id === segmentId) || null;
  }

  function buildPredictionBrief(segmentId) {
    const snapshot = getSegmentSnapshot(segmentId);
    const future = (state.predictionAnalysis && state.predictionAnalysis.future) || [];
    const causes = (state.causes && state.causes.ranking) || [];
    const metrics = (state.predictionAnalysis && state.predictionAnalysis.metrics) || { mape: '-', mae: '-' };
    const peak = future.reduce((best, row) => (row.pred_congestion_index > best.pred_congestion_index ? row : best), future[0] || null);
    const topCause = causes[0];
    return {
      level: snapshot ? snapshot.pred_congestion_level : '-',
      index: snapshot ? snapshot.pred_congestion_index : '-',
      flow: snapshot ? snapshot.pred_flow_veh_15m : '-',
      confidencePct: snapshot ? `${Math.round((snapshot.confidence || 0) * 100)}%` : '-',
      topCause: topCause ? `${topCause.cause}(${topCause.contribution_pct}%)` : '-',
      peakTime: peak ? toLabel(peak.timestamp) : '-',
      peakLevel: peak ? peak.pred_congestion_level : '-',
      mape: metrics.mape,
      mae: metrics.mae,
    };
  }

  function setCompareStatus(text) {
    const el = byId('compareStatus');
    if (el) el.textContent = text;
  }

  function getSearchMatches(keyword) {
    const all = state.overview.map((item) => item.segment_id);
    const q = String(keyword || '').trim().toLowerCase();
    if (!q) return all;
    return all.filter((segmentId) => segmentId.toLowerCase().includes(q));
  }

  function renderSegmentSearchHint(keyword) {
    const hint = byId('segmentSearchHint');
    if (!hint) return;
    const allCount = state.overview.length;
    const q = String(keyword || '').trim();
    if (!q) {
      hint.textContent = `可输入关键词快速定位目标路段（当前 ${allCount} 条路段）。`;
      return;
    }
    const matched = getSearchMatches(q);
    if (!matched.length) {
      hint.textContent = `未找到包含 "${q}" 的路段，请换关键词。`;
      return;
    }
    const preview = matched.slice(0, 4).join('、');
    hint.textContent = `匹配到 ${matched.length} 条：${preview}${matched.length > 4 ? '...' : ''}`;
  }

  async function locateSegmentBySearch() {
    const keyword = state.segmentSearchKeyword;
    const q = String(keyword || '').trim();
    if (!q) {
      setStatus('请先输入路段关键词，再执行搜索定位。');
      return;
    }
    const matched = getSearchMatches(q);
    if (!matched.length) {
      setStatus(`没有匹配 "${q}" 的路段。`);
      renderSegmentSearchHint(q);
      return;
    }
    const target = matched[0];
    const segmentSelect = byId('segmentSelect');
    if (segmentSelect) segmentSelect.value = target;
    await onSegmentChange(target, '搜索定位');
  }

  async function addCurrentSegmentToComparison() {
    const segmentId = byId('segmentSelect') ? byId('segmentSelect').value : state.selectedSegmentId;
    if (!segmentId) {
      setStatus('请先选择路段，再加入对比。');
      return;
    }
    const next = [segmentId, ...state.comparisonSegmentIds.filter((id) => id !== segmentId)];
    state.comparisonSegmentIds = normalizeComparisonSegmentIds(next);
    fillCompareSegmentSelect();
    await loadComparisonPredictions();
    activatePage('prediction');
    renderPredictionCharts();
    setStatus(`已将 ${segmentId} 加入多路段对比（共 ${state.comparisonSegmentIds.length} 条）`);
  }

  function defaultComparisonSegmentIds() {
    const all = state.overview.map((item) => item.segment_id);
    if (!all.length) return [];
    const selected = state.selectedSegmentId || all[0];
    const rest = all.filter((item) => item !== selected);
    return [selected, ...rest.slice(0, 2)];
  }

  function normalizeComparisonSegmentIds(ids) {
    const all = new Set(state.overview.map((item) => item.segment_id));
    const unique = [];
    (ids || []).forEach((item) => {
      if (!item || !all.has(item) || unique.includes(item)) return;
      unique.push(item);
    });
    if (state.selectedSegmentId && all.has(state.selectedSegmentId) && !unique.includes(state.selectedSegmentId)) {
      unique.unshift(state.selectedSegmentId);
    }
    return unique.slice(0, 5);
  }

  function fillCompareSegmentSelect() {
    const select = byId('compareSegmentSelect');
    if (!select) return;
    const options = state.overview.map((item) => item.segment_id);
    if (!state.comparisonSegmentIds.length) {
      state.comparisonSegmentIds = defaultComparisonSegmentIds();
    }
    state.comparisonSegmentIds = normalizeComparisonSegmentIds(state.comparisonSegmentIds);
    select.innerHTML = options.map((segmentId) => `<option value="${segmentId}">${segmentId}</option>`).join('');
    Array.from(select.options).forEach((opt) => {
      opt.selected = state.comparisonSegmentIds.includes(opt.value);
    });
  }

  function readCompareSelectionFromUi() {
    const select = byId('compareSegmentSelect');
    if (!select) return [];
    return Array.from(select.selectedOptions || []).map((opt) => opt.value).filter(Boolean);
  }

  async function loadComparisonPredictions() {
    const ids = normalizeComparisonSegmentIds(state.comparisonSegmentIds.length ? state.comparisonSegmentIds : defaultComparisonSegmentIds());
    state.comparisonSegmentIds = ids;
    fillCompareSegmentSelect();
    if (!ids.length) {
      state.comparisonPredictions = {};
      setCompareStatus('暂无可对比路段');
      return;
    }

    state.isLoadingComparison = true;
    setControlsBusy(state.isRefreshing || state.isSwitchingSegment);
    setCompareStatus(`正在更新 ${ids.length} 个路段的预测...`);
    try {
      const rows = await Promise.all(ids.map(async (segmentId) => {
        if (segmentId === state.selectedSegmentId && state.predictionAnalysis && Array.isArray(state.predictionAnalysis.future)) {
          return [segmentId, state.predictionAnalysis.future];
        }
        try {
          const data = await apiRequest(`/api/v1/analytics/segments/${segmentId}/prediction?history_points=8&future_points=8&window_minutes=${state.windowMinutes}`);
          return [segmentId, data.future || []];
        } catch (_err) {
          state.useFallback = true;
          return [segmentId, buildMockPrediction(segmentId).future || []];
        }
      }));
      state.comparisonPredictions = Object.fromEntries(rows);
      setCompareStatus(`已更新 ${ids.length} 个路段对比`);
    } finally {
      state.isLoadingComparison = false;
      setControlsBusy(state.isRefreshing || state.isSwitchingSegment);
    }
  }

  function setControlsBusy(busy, mode) {
    const refreshBtn = byId('refreshBtn');
    if (refreshBtn) {
      refreshBtn.disabled = busy;
      if (!busy) {
        refreshBtn.textContent = '刷新数据';
      } else if (mode === 'switch') {
        refreshBtn.textContent = '切换中...';
      } else {
        refreshBtn.textContent = '刷新中...';
      }
    }
    const segmentSelect = byId('segmentSelect');
    if (segmentSelect) segmentSelect.disabled = busy;
    const windowSelect = byId('windowSelect');
    if (windowSelect) windowSelect.disabled = busy;
    const predictNowBtn = byId('predictNowBtn');
    if (predictNowBtn) predictNowBtn.disabled = busy;
    const segmentSearch = byId('segmentSearch');
    if (segmentSearch) segmentSearch.disabled = busy;
    const locateSegmentBtn = byId('locateSegmentBtn');
    if (locateSegmentBtn) locateSegmentBtn.disabled = busy;
    const addToCompareBtn = byId('addToCompareBtn');
    if (addToCompareBtn) addToCompareBtn.disabled = busy || state.isLoadingComparison;
    const compareSelect = byId('compareSegmentSelect');
    if (compareSelect) compareSelect.disabled = busy || state.isLoadingComparison;
    const applyCompareBtn = byId('applyCompareBtn');
    if (applyCompareBtn) applyCompareBtn.disabled = busy || state.isLoadingComparison;
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function segmentSeed(segmentId) {
    const digits = String(segmentId || '').replace(/\D/g, '');
    if (!digits) return 17;
    return Number(digits.slice(-2));
  }

  function toLabel(ts) {
    const date = new Date(ts);
    if (Number.isNaN(date.getTime())) return String(ts);
    const hh = String(date.getHours()).padStart(2, '0');
    const mm = String(date.getMinutes()).padStart(2, '0');
    return `${hh}:${mm}`;
  }

  function toDateTimeLabel(ts) {
    const date = new Date(ts);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleString('zh-CN', { hour12: false });
  }

  function levelByIndex(index) {
    if (index >= 0.80) return '严重拥堵';
    if (index >= 0.60) return '拥堵';
    if (index >= 0.35) return '缓行';
    return '畅通';
  }

  function levelColor(level) {
    if (level === '严重拥堵') return '#e34d59';
    if (level === '拥堵') return '#ff9f1a';
    if (level === '缓行') return '#2a83ff';
    return '#00a870';
  }

  function normalizeLevel(value) {
    const text = String(value || '').toLowerCase();
    if (text.includes('critical') || text.includes('severe') || text.includes('严重')) return '严重拥堵';
    if (text.includes('high') || text.includes('拥堵')) return '拥堵';
    if (text.includes('elevated') || text.includes('moderate') || text.includes('缓')) return '缓行';
    if (text.includes('normal') || text.includes('畅通')) return '畅通';
    return '缓行';
  }

  function safeChart(id) {
    const container = byId(id);
    if (!container) return null;
    if (!hasEcharts()) {
      container.innerHTML = '<div class="chart-fallback">ECharts 未加载，无法渲染图表。</div>';
      return null;
    }
    if (!state.charts[id]) {
      state.charts[id] = window.echarts.init(container);
    }
    return state.charts[id];
  }

  function renderChart(id, option) {
    const instance = safeChart(id);
    if (!instance) return;
    instance.setOption(option, true);
  }

  async function apiRequest(path) {
    const base = (state.apiBase || '').replace(/\/$/, '');
    const res = await fetch(`${base}${path}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return res.json();
  }

  function createDomesticProviderFactories() {
    return [
      {
        name: '高德路网',
        create: () => window.L.tileLayer(
          'https://wprd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&style=8&x={x}&y={y}&z={z}',
          {
            subdomains: ['1', '2', '3', '4'],
            maxZoom: 18,
            attribution: '&copy; 高德地图',
          }
        ),
      },
      {
        name: '高德标准',
        create: () => window.L.tileLayer(
          'https://wprd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&style=7&x={x}&y={y}&z={z}',
          {
            subdomains: ['1', '2', '3', '4'],
            maxZoom: 18,
            attribution: '&copy; 高德地图',
          }
        ),
      },
      {
        name: 'GeoQ 中国浅色',
        create: () => window.L.tileLayer(
          'https://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineCommunity/MapServer/tile/{z}/{y}/{x}',
          {
            maxZoom: 18,
            attribution: '&copy; GeoQ',
          }
        ),
      },
      {
        name: 'GeoQ 中国暖色',
        create: () => window.L.tileLayer(
          'https://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineStreetWarm/MapServer/tile/{z}/{y}/{x}',
          {
            maxZoom: 18,
            attribution: '&copy; GeoQ',
          }
        ),
      },
    ];
  }

  function mountDomesticBaseLayer(map, applyLayer, setProviderName, onAllFailed) {
    const providerFactories = createDomesticProviderFactories();
    const switchProvider = (index) => {
      if (index < 0 || index >= providerFactories.length) {
        if (typeof onAllFailed === 'function') onAllFailed();
        return;
      }

      const provider = providerFactories[index];
      const layer = provider.create();
      let tileErrorCount = 0;

      layer.on('tileerror', () => {
        tileErrorCount += 1;
        if (tileErrorCount >= 8) {
          switchProvider(index + 1);
        }
      });

      layer.on('load', () => {
        if (typeof setProviderName === 'function') setProviderName(provider.name);
      });

      try {
        applyLayer(layer);
      } catch (_err) {
        switchProvider(index + 1);
      }
    };

    switchProvider(0);
  }

  function getPredictionFuture() {
    return (state.predictionAnalysis && state.predictionAnalysis.future) || [];
  }

  function getPredictionFrameIndex() {
    const future = getPredictionFuture();
    if (!future.length) return 0;
    const max = future.length - 1;
    return clamp(Number(state.predictionPlayback.frameIndex || 0), 0, max);
  }

  function updatePredictionFrameLabel() {
    const future = getPredictionFuture();
    const slider = byId('predMapFrame');
    const label = byId('predMapFrameLabel');
    if (!slider || !label) return;

    if (!future.length) {
      slider.max = '0';
      slider.value = '0';
      label.textContent = '无未来预测';
      return;
    }

    const frame = getPredictionFrameIndex();
    const item = future[frame];
    slider.max = String(future.length - 1);
    slider.value = String(frame);
    label.textContent = `第${frame + 1}/${future.length}帧 ${toLabel(item.timestamp)}`;
  }

  function stopPredictionPlayback() {
    const timer = state.predictionPlayback.timer;
    if (!timer) return;
    clearInterval(timer);
    state.predictionPlayback.timer = null;
  }

  function startPredictionPlayback() {
    const future = getPredictionFuture();
    if (!future.length) return;
    if (state.predictionPlayback.timer) return;
    state.predictionPlayback.timer = setInterval(() => {
      const max = future.length - 1;
      state.predictionPlayback.frameIndex = (getPredictionFrameIndex() + 1) % (max + 1);
      renderPredictionMap();
      renderPredictionCharts();
    }, 1200);
  }

  function buildMockOverview() {
    const geometryMap = getSegmentGeometryMap();
    return Object.keys(geometryMap).map((segmentId, idx) => {
      const seed = segmentSeed(segmentId);
      const flow = Math.round(180 + (seed % 35) * 15 + idx * 8);
      const congestionIndex = clamp(0.28 + (seed % 9) * 0.075, 0.2, 0.95);
      const gridId = Object.keys(gridCenters)[idx % Object.keys(gridCenters).length];
      return {
        segment_id: segmentId,
        grid_id: gridId,
        flow_veh_15m: flow,
        congestion_index: Number(congestionIndex.toFixed(3)),
        congestion_level: levelByIndex(congestionIndex),
        updated_at: new Date().toISOString(),
      };
    });
  }

  function buildMockTrend(segmentId) {
    const base = state.overview.find((item) => item.segment_id === segmentId) || state.overview[0];
    const now = Date.now();
    const points = [];
    const seed = segmentSeed(segmentId);
    for (let i = 0; i < 12; i += 1) {
      const ts = new Date(now - (11 - i) * state.windowMinutes * 60000).toISOString();
      const season = Math.sin((i + seed) * 0.8) * 0.09;
      const flow = (base.flow_veh_15m || 300) * (1 + season);
      const congestion = clamp((base.congestion_index || 0.5) * (1 + season * 0.8), 0.18, 0.97);
      points.push({
        timestamp: ts,
        flow_veh_15m: Number(flow.toFixed(1)),
        congestion_index: Number(congestion.toFixed(3)),
      });
    }
    return { segment_id: segmentId, window_minutes: state.windowMinutes, points };
  }

  function buildMockCauses(segmentId) {
    const seed = segmentSeed(segmentId);
    const now = Date.now();
    const timeline = [];
    const buckets = { weather: 0, holiday: 0, incident: 0, other: 0 };

    for (let i = 0; i < 8; i += 1) {
      const ts = new Date(now - (7 - i) * state.windowMinutes * 60000).toISOString();
      const weather = 22 + Math.sin((i + seed) * 0.9) * 4;
      const holiday = 24 + Math.cos((i + seed) * 0.6) * 5;
      const incident = 41 + Math.sin((i + seed) * 0.7) * 6;
      const other = 100 - weather - holiday - incident;
      const norm = {
        weather_pct: Number((weather / (weather + holiday + incident + other) * 100).toFixed(1)),
        holiday_pct: Number((holiday / (weather + holiday + incident + other) * 100).toFixed(1)),
        incident_pct: Number((incident / (weather + holiday + incident + other) * 100).toFixed(1)),
        other_pct: Number((other / (weather + holiday + incident + other) * 100).toFixed(1)),
      };
      buckets.weather += norm.weather_pct;
      buckets.holiday += norm.holiday_pct;
      buckets.incident += norm.incident_pct;
      buckets.other += norm.other_pct;
      timeline.push({ timestamp: ts, ...norm });
    }

    const ranking = [
      { cause: '天气', contribution_pct: Number((buckets.weather / 8).toFixed(1)) },
      { cause: '节假日', contribution_pct: Number((buckets.holiday / 8).toFixed(1)) },
      { cause: '交通事故', contribution_pct: Number((buckets.incident / 8).toFixed(1)) },
      { cause: '其他', contribution_pct: Number((buckets.other / 8).toFixed(1)) },
    ].sort((a, b) => b.contribution_pct - a.contribution_pct);

    return {
      segment_id: segmentId,
      window_minutes: state.windowMinutes,
      timeline,
      ranking,
      summary: `当前路段主因是${ranking[0].cause}，建议优先针对${ranking[0].cause}制定疏导策略。`,
    };
  }

  function buildMockPrediction(segmentId) {
    const trend = buildMockTrend(segmentId);
    const endPoint = trend.points[trend.points.length - 1];
    const now = new Date(endPoint.timestamp).getTime();
    const seed = segmentSeed(segmentId);

    const backtest = trend.points.map((point, idx) => {
      const pred = point.flow_veh_15m * (1 + Math.cos((idx + seed) * 0.5) * 0.03);
      const absError = Math.abs(pred - point.flow_veh_15m);
      const ape = absError / Math.max(point.flow_veh_15m, 1) * 100;
      return {
        timestamp: point.timestamp,
        actual_flow_veh_15m: Number(point.flow_veh_15m.toFixed(1)),
        pred_flow_veh_15m: Number(pred.toFixed(1)),
        abs_error: Number(absError.toFixed(2)),
        ape: Number(ape.toFixed(2)),
      };
    });

    const future = [];
    for (let i = 1; i <= 8; i += 1) {
      const ts = new Date(now + i * state.windowMinutes * 60000).toISOString();
      const rise = i / 8 * 0.12;
      const noise = Math.sin((i + seed) * 0.65) * 0.04;
      const predFlow = endPoint.flow_veh_15m * (1 + rise + noise);
      const predIndex = clamp(endPoint.congestion_index * (1 + rise * 0.85 + noise), 0.2, 0.99);
      future.push({
        timestamp: ts,
        pred_flow_veh_15m: Number(predFlow.toFixed(1)),
        pred_congestion_index: Number(predIndex.toFixed(3)),
        pred_congestion_level: levelByIndex(predIndex),
      });
    }

    const mae = backtest.reduce((acc, cur) => acc + cur.abs_error, 0) / backtest.length;
    const mape = backtest.reduce((acc, cur) => acc + cur.ape, 0) / backtest.length;
    const rmse = Math.sqrt(backtest.reduce((acc, cur) => acc + cur.abs_error * cur.abs_error, 0) / backtest.length);

    return {
      segment_id: segmentId,
      window_minutes: state.windowMinutes,
      generated_at: new Date().toISOString(),
      backtest,
      future,
      metrics: {
        mae: Number(mae.toFixed(2)),
        mape: Number(mape.toFixed(2)),
        rmse: Number(rmse.toFixed(2)),
      },
    };
  }

  function buildMockModelErrors() {
    return [
      { model_id: 'mock:stgnn', model_name: 'STGNN', family: 'stgnn', mae: 10.6, mape: 8.3, rmse: 13.2, score: 1.0 },
      { model_id: 'mock:gru', model_name: 'GRU', family: 'deep', mae: 11.8, mape: 9.2, rmse: 14.7, score: 0.902 },
      { model_id: 'mock:lstm', model_name: 'LSTM', family: 'deep', mae: 12.4, mape: 10.1, rmse: 15.5, score: 0.822 },
      { model_id: 'mock:tree', model_name: 'TREE', family: 'baseline', mae: 13.1, mape: 11.2, rmse: 16.9, score: 0.741 },
    ];
  }

  function buildMockSegmentPredictionSnapshots() {
    const list = state.overview.map((item, idx) => {
      const rand = Math.random();
      let pred_index;
      if (rand < 0.25) {
        pred_index = clamp(Math.random() * 0.35, 0.1, 0.35);
      } else if (rand < 0.65) {
        pred_index = clamp(0.35 + Math.random() * 0.25, 0.35, 0.60);
      } else if (rand < 0.95) {
        pred_index = clamp(0.60 + Math.random() * 0.20, 0.60, 0.80);
      } else {
        pred_index = clamp(0.80 + Math.random() * 0.19, 0.80, 0.99);
      }
      const confidence = 0.60 + Math.random() * 0.38;
      return {
        segment_id: item.segment_id,
        pred_flow_veh_15m: Number((Number(item.flow_veh_15m || 200) * (0.9 + Math.random() * 0.4)).toFixed(1)),
        pred_congestion_index: Number(pred_index.toFixed(3)),
        pred_congestion_level: levelByIndex(pred_index),
        confidence: Number(confidence.toFixed(3)),
        window_start: new Date().toISOString(),
        window_end: new Date(Date.now() + state.windowMinutes * 60000).toISOString(),
      };
    });
    list.sort((a, b) => b.pred_congestion_index - a.pred_congestion_index);
    return list;
  }

  function buildMockSegmentReport(segmentId) {
    const causes = state.causes && state.causes.ranking ? state.causes.ranking : [];
    const top = causes[0] || { cause: '交通事故', contribution_pct: 40 };
    const pred = state.predictionAnalysis || buildMockPrediction(segmentId);
    const futurePeak = (pred.future || []).reduce((best, row) => (row.pred_flow_veh_15m > (best.pred_flow_veh_15m || 0) ? row : best), {});
    return {
      segment_id: segmentId,
      generated_at: new Date().toISOString(),
      window_minutes: state.windowMinutes,
      findings: [
        `当前路段 ${segmentId} 在近${state.windowMinutes}分钟窗口内流量处于中高位。`,
        `拥堵主因是${top.cause}（贡献约${top.contribution_pct}%）。`,
        `未来峰值预计为 ${futurePeak.pred_flow_veh_15m || '-'} 辆/15分钟，等级 ${futurePeak.pred_congestion_level || '-' }。`,
        '建议结合高峰期信号配时与分流策略降低拥堵风险。',
      ],
      actions: [
        '高风险时段启用潮汐车道或绕行引导。',
        `针对${top.cause}建立专项干预机制。`,
        '每周复盘模型误差并迭代特征工程。',
      ],
    };
  }

  function buildMockEvents() {
    return [
      {
        event_id: 'event-bridge',
        segment_id: 'SEG-4001',
        name: '高架桥施工',
        grid_id: 'GRID-D1',
        severity: 'High',
        confidence: 0.93,
        window_start: new Date(Date.now() - 45 * 60000).toISOString(),
        window_end: new Date(Date.now() + 30 * 60000).toISOString(),
      },
      {
        event_id: 'event-stadium',
        segment_id: 'SEG-2002',
        name: '体育场散场',
        grid_id: 'GRID-B2',
        severity: 'Critical',
        confidence: 0.96,
        window_start: new Date(Date.now() - 60 * 60000).toISOString(),
        window_end: new Date(Date.now() + 20 * 60000).toISOString(),
      },
      {
        event_id: 'event-market',
        segment_id: 'SEG-1003',
        name: '商圈活动',
        grid_id: 'GRID-A3',
        severity: 'Elevated',
        confidence: 0.83,
        window_start: new Date(Date.now() - 30 * 60000).toISOString(),
        window_end: new Date(Date.now() + 40 * 60000).toISOString(),
      },
    ];
  }

  function buildMockHeatLayer() {
    return {
      layer_id: 'mock-heat-layer',
      generated_at: new Date().toISOString(),
      segments: state.overview.map((item) => ({
        segment_id: item.segment_id,
        grid_id: item.grid_id,
        heat_score: item.congestion_index,
        updated_at: item.updated_at,
      })),
    };
  }

  function fillSegmentSelect() {
    const select = byId('segmentSelect');
    const options = state.overview.map((item) => item.segment_id);
    select.innerHTML = options.map((segmentId) => `<option value="${segmentId}">${segmentId}</option>`).join('');
    if (!options.includes(state.selectedSegmentId)) {
      state.selectedSegmentId = options[0] || '';
    }
    select.value = state.selectedSegmentId;
    state.comparisonSegmentIds = normalizeComparisonSegmentIds(state.comparisonSegmentIds.length ? state.comparisonSegmentIds : defaultComparisonSegmentIds());
    fillCompareSegmentSelect();
    renderSegmentSearchHint(state.segmentSearchKeyword);
  }

  function updateSelectionTag() {
    byId('selectedSegmentTag').textContent = state.selectedSegmentId || '未选择';
    const row = state.overview.find((item) => item.segment_id === state.selectedSegmentId);
    byId('selectedLevelTag').textContent = row ? row.congestion_level : '未计算';
    const snapshot = (state.segmentPredictionSnapshots || []).find((item) => item.segment_id === state.selectedSegmentId);
    byId('selectedPredFlowTag').textContent = snapshot ? `${snapshot.pred_flow_veh_15m} 辆/15分钟` : '-';
    byId('selectedPredIndexTag').textContent = snapshot ? String(snapshot.pred_congestion_index) : '-';
    byId('selectedUpdatedAtTag').textContent = toDateTimeLabel(state.lastRefreshAt || (row && row.updated_at));
  }

  function focusSelectedSegmentOnMaps(segmentId) {
    if (!segmentId) return;

    const mapLine = state.mapRefs.segmentLines[segmentId];
    if (mapLine && state.map && typeof mapLine.getBounds === 'function') {
      if (typeof mapLine.bringToFront === 'function') mapLine.bringToFront();
      mapLine.setStyle({ weight: 11, opacity: 1 });
      state.map.fitBounds(mapLine.getBounds(), { padding: [80, 80], maxZoom: 15 });
      if (typeof mapLine.openPopup === 'function') mapLine.openPopup();
      setTimeout(() => {
        mapLine.setStyle({ weight: 8, opacity: 0.92 });
      }, 700);
    }

    const predLine = state.mapRefs.predictionSegmentLines[segmentId];
    if (predLine && state.predictionMap && typeof predLine.getBounds === 'function') {
      if (typeof predLine.bringToFront === 'function') predLine.bringToFront();
      predLine.setStyle({ weight: 10, opacity: 1 });
      state.predictionMap.fitBounds(predLine.getBounds(), { padding: [70, 70], maxZoom: 15 });
      if (typeof predLine.openPopup === 'function') predLine.openPopup();
      setTimeout(() => {
        predLine.setStyle({ weight: 7, opacity: 0.9 });
      }, 700);
    }
  }

  function renderKpis() {
    const risky = state.overview.filter((item) => item.congestion_index >= 0.6);
    const severe = state.overview.filter((item) => item.congestion_index >= 0.8);
    const avgFlow = state.overview.length
      ? state.overview.reduce((acc, cur) => acc + Number(cur.flow_veh_15m || 0), 0) / state.overview.length
      : 0;

    const cards = [
      { name: '拥堵路段数', value: risky.length },
      { name: '严重拥堵路段数', value: severe.length },
      { name: '路段平均流量(辆/15分钟)', value: avgFlow.toFixed(1) },
      { name: '当前分析路段', value: state.selectedSegmentId || '-' },
    ];

    byId('kpiGrid').innerHTML = cards
      .map((item) => `<div class="kpi"><div class="name">${item.name}</div><div class="value">${item.value}</div></div>`)
      .join('');
  }

  function renderPredictionKpis() {
    const metrics = (state.predictionAnalysis && state.predictionAnalysis.metrics) || { mae: 0, mape: 0, rmse: 0 };
    const future = (state.predictionAnalysis && state.predictionAnalysis.future) || [];
    const peak = future.reduce((best, row) => (row.pred_flow_veh_15m > best.pred_flow_veh_15m ? row : best), future[0] || {
      pred_flow_veh_15m: 0,
      pred_congestion_level: '-',
    });

    const cards = [
      { name: 'MAE', value: metrics.mae },
      { name: 'MAPE(%)', value: metrics.mape },
      { name: 'RMSE', value: metrics.rmse },
      { name: '未来峰值拥堵等级', value: peak.pred_congestion_level || '-' },
    ];

    byId('predictionMetricCards').innerHTML = cards
      .map((item) => `<div class="kpi"><div class="name">${item.name}</div><div class="value">${item.value}</div></div>`)
      .join('');
  }

  function renderFlowChart() {
    const rows = [...state.overview].sort((a, b) => b.flow_veh_15m - a.flow_veh_15m);
    renderChart('segmentFlowChart', {
      tooltip: { trigger: 'axis' },
      legend: { data: ['流量', '拥堵指数'], top: 0 },
      grid: { left: 52, right: 48, top: 42, bottom: 48 },
      xAxis: {
        type: 'category',
        data: rows.map((item) => item.segment_id),
        axisLabel: { interval: 0, rotate: 20 },
        name: '路段',
      },
      yAxis: [
        { type: 'value', name: '流量(辆/15分钟)' },
        { type: 'value', name: '拥堵指数', min: 0, max: 1 },
      ],
      series: [
        {
          name: '流量',
          type: 'bar',
          barMaxWidth: 26,
          data: rows.map((item) => Number(item.flow_veh_15m || 0)),
          itemStyle: { color: '#2a83ff' },
        },
        {
          name: '拥堵指数',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          symbol: 'circle',
          data: rows.map((item) => Number(item.congestion_index || 0)),
          itemStyle: { color: '#e34d59' },
          lineStyle: { width: 2 },
        },
      ],
    });
  }

  function renderTrendChart() {
    const points = (state.trend && state.trend.points) || [];
    renderChart('segmentTrendChart', {
      tooltip: { trigger: 'axis' },
      legend: { data: ['流量', '拥堵指数'], top: 0 },
      grid: { left: 52, right: 52, top: 42, bottom: 38 },
      xAxis: {
        type: 'category',
        data: points.map((item) => toLabel(item.timestamp)),
        name: '时间',
      },
      yAxis: [
        { type: 'value', name: '流量(辆/15分钟)' },
        { type: 'value', name: '拥堵指数', min: 0, max: 1 },
      ],
      series: [
        {
          name: '流量',
          type: 'line',
          smooth: true,
          data: points.map((item) => Number(item.flow_veh_15m || 0)),
          areaStyle: { color: 'rgba(42,131,255,0.15)' },
          itemStyle: { color: '#2a83ff' },
        },
        {
          name: '拥堵指数',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          data: points.map((item) => Number(item.congestion_index || 0)),
          itemStyle: { color: '#ff9f1a' },
          lineStyle: { type: 'dashed' },
        },
      ],
    });
  }

  function renderCauseCharts() {
    const timeline = (state.causes && state.causes.timeline) || [];
    renderChart('causeTimelineChart', {
      tooltip: { trigger: 'axis' },
      legend: { data: ['天气', '节假日', '交通事故', '其他'], top: 0 },
      grid: { left: 52, right: 20, top: 42, bottom: 38 },
      xAxis: { type: 'category', data: timeline.map((item) => toLabel(item.timestamp)), name: '时间' },
      yAxis: { type: 'value', min: 0, max: 100, name: '贡献度(%)' },
      series: [
        { name: '天气', type: 'bar', stack: 'cause', data: timeline.map((item) => item.weather_pct) },
        { name: '节假日', type: 'bar', stack: 'cause', data: timeline.map((item) => item.holiday_pct) },
        { name: '交通事故', type: 'bar', stack: 'cause', data: timeline.map((item) => item.incident_pct) },
        { name: '其他', type: 'bar', stack: 'cause', data: timeline.map((item) => item.other_pct) },
      ],
    });

    const ranking = (state.causes && state.causes.ranking) || [];
    renderChart('causeRankingChart', {
      tooltip: { trigger: 'axis' },
      grid: { left: 70, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'value', name: '贡献度(%)' },
      yAxis: { type: 'category', data: ranking.map((item) => item.cause) },
      series: [{ type: 'bar', data: ranking.map((item) => item.contribution_pct), itemStyle: { color: '#0a6cff' } }],
    });

    const summary = (state.causes && state.causes.summary) || '暂无归因结果';
    const top = ranking[0];
    const second = ranking[1];
    byId('causeSummary').innerHTML = [
      `<p><b>主导原因：</b>${top ? `${top.cause}（${top.contribution_pct}%）` : '-'}</p>`,
      `<p><b>次要原因：</b>${second ? `${second.cause}（${second.contribution_pct}%）` : '-'}</p>`,
      `<p><b>结论：</b>${summary}</p>`,
      '<p><b>建议动作：</b>对高贡献原因优先处置，结合路段实时流量做分流与信号配时。</p>',
    ].join('');
  }

  function renderPredictionCharts() {
    const prediction = state.predictionAnalysis || { future: [], backtest: [], metrics: { mae: 0, mape: 0, rmse: 0 } };
    const future = prediction.future || [];
    const backtest = prediction.backtest || [];
    const modelErrors = state.modelErrors || [];
    const snapshots = state.segmentPredictionSnapshots || [];

    const selectedSnapshot = snapshots.find((item) => item.segment_id === state.selectedSegmentId);
    const brief = buildPredictionBrief(state.selectedSegmentId);
    byId('predictionFocusBanner').innerHTML = selectedSnapshot
      ? `<h3>当前路段预测结论：${selectedSnapshot.segment_id} · <span class="sev-${selectedSnapshot.pred_congestion_level}">${selectedSnapshot.pred_congestion_level}</span></h3>
         <p>未来一时窗预测流量 ${selectedSnapshot.pred_flow_veh_15m} 辆/15分钟，拥堵指数 ${selectedSnapshot.pred_congestion_index}，置信度 ${Math.round((selectedSnapshot.confidence || 0) * 100)}%。</p>`
      : '<h3>当前路段预测结论：暂无</h3><p>请先刷新数据并选择路段。</p>';
    byId('predictionQuickBrief').innerHTML = [
      `<h3>路段 ${state.selectedSegmentId || '-'} 预测简报</h3>`,
      '<div class="brief-grid">',
      `<div class="brief-item"><div class="brief-key">预测拥堵等级</div><div class="brief-value sev-${brief.level}">${brief.level}</div></div>`,
      `<div class="brief-item"><div class="brief-key">未来一窗拥堵指数</div><div class="brief-value">${brief.index}</div></div>`,
      `<div class="brief-item"><div class="brief-key">未来一窗预测流量</div><div class="brief-value">${brief.flow}</div></div>`,
      `<div class="brief-item"><div class="brief-key">预测置信度</div><div class="brief-value">${brief.confidencePct}</div></div>`,
      `<div class="brief-item"><div class="brief-key">拥堵主因</div><div class="brief-value">${brief.topCause}</div></div>`,
      `<div class="brief-item"><div class="brief-key">未来峰值时间</div><div class="brief-value">${brief.peakTime}</div></div>`,
      `<div class="brief-item"><div class="brief-key">未来峰值等级</div><div class="brief-value sev-${brief.peakLevel}">${brief.peakLevel}</div></div>`,
      `<div class="brief-item"><div class="brief-key">MAPE / MAE</div><div class="brief-value">${brief.mape} / ${brief.mae}</div></div>`,
      '</div>',
    ].join('');

    const compareIds = state.comparisonSegmentIds.length ? state.comparisonSegmentIds : defaultComparisonSegmentIds();
    const comparePredictions = state.comparisonPredictions || {};
    const baseSeries = comparePredictions[compareIds[0]] || future;
    const compareXAxis = (baseSeries || []).map((item) => toLabel(item.timestamp));
    renderChart('multiSegmentCompareChart', {
      tooltip: { trigger: 'axis' },
      legend: { type: 'scroll', top: 0, data: compareIds.map((id) => `${id} 拥堵指数`) },
      grid: { left: 56, right: 20, top: 46, bottom: 38 },
      xAxis: { type: 'category', data: compareXAxis, name: '未来时间' },
      yAxis: { type: 'value', min: 0, max: 1, name: '拥堵指数' },
      series: compareIds.map((segmentId, idx) => {
        const rows = comparePredictions[segmentId] || [];
        const colorPalette = ['#e34d59', '#2a83ff', '#00a870', '#ff9f1a', '#7a5cff'];
        return {
          name: `${segmentId} 拥堵指数`,
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 7,
          lineStyle: { width: segmentId === state.selectedSegmentId ? 4 : 2.5 },
          itemStyle: { color: colorPalette[idx % colorPalette.length] },
          data: rows.map((item) => Number(item.pred_congestion_index || 0)),
        };
      }),
    });

    renderChart('modelErrorCompareChart', {
      tooltip: { trigger: 'axis' },
      legend: { data: ['MAPE', 'MAE'], top: 0 },
      grid: { left: 52, right: 52, top: 42, bottom: 38 },
      xAxis: { type: 'category', data: modelErrors.map((item) => item.model_name), name: '模型' },
      yAxis: [
        { type: 'value', name: 'MAPE(%)' },
        { type: 'value', name: 'MAE' },
      ],
      series: [
        { name: 'MAPE', type: 'bar', data: modelErrors.map((item) => item.mape), itemStyle: { color: '#7a5cff' } },
        { name: 'MAE', type: 'line', yAxisIndex: 1, smooth: true, data: modelErrors.map((item) => item.mae), itemStyle: { color: '#ff9f1a' } },
      ],
    });

    const topRows = snapshots.slice(0, 12);
    renderChart('allSegmentPredChart', {
      tooltip: { trigger: 'axis' },
      legend: { data: ['预测流量', '拥堵指数'], top: 0 },
      grid: { left: 56, right: 52, top: 42, bottom: 48 },
      xAxis: { type: 'category', data: topRows.map((item) => item.segment_id), name: '路段' },
      yAxis: [
        { type: 'value', name: '流量(辆/15分钟)' },
        { type: 'value', name: '拥堵指数', min: 0, max: 1 },
      ],
      series: [
        { name: '预测流量', type: 'bar', data: topRows.map((item) => item.pred_flow_veh_15m), itemStyle: { color: '#1f88ff' } },
        { name: '拥堵指数', type: 'line', yAxisIndex: 1, smooth: true, data: topRows.map((item) => item.pred_congestion_index), itemStyle: { color: '#e34d59' } },
      ],
    });

    renderChart('futureFlowChart', {
      tooltip: { trigger: 'axis' },
      grid: { left: 52, right: 20, top: 24, bottom: 38 },
      xAxis: { type: 'category', data: future.map((item) => toLabel(item.timestamp)), name: '未来时间' },
      yAxis: { type: 'value', name: '预测流量(辆/15分钟)' },
      series: [{ type: 'line', smooth: true, data: future.map((item) => item.pred_flow_veh_15m), itemStyle: { color: '#00a870' } }],
    });

    renderChart('compareChart', {
      tooltip: { trigger: 'axis' },
      legend: { data: ['真实值', '预测值'], top: 0 },
      grid: { left: 52, right: 20, top: 42, bottom: 38 },
      xAxis: { type: 'category', data: backtest.map((item) => toLabel(item.timestamp)), name: '历史时间' },
      yAxis: { type: 'value', name: '流量(辆/15分钟)' },
      series: [
        { name: '真实值', type: 'line', smooth: true, data: backtest.map((item) => item.actual_flow_veh_15m), itemStyle: { color: '#2a83ff' } },
        { name: '预测值', type: 'line', smooth: true, data: backtest.map((item) => item.pred_flow_veh_15m), itemStyle: { color: '#e34d59' } },
      ],
    });

    renderChart('errorChart', {
      tooltip: { trigger: 'axis' },
      legend: { data: ['绝对误差', 'APE%'], top: 0 },
      grid: { left: 52, right: 52, top: 42, bottom: 38 },
      xAxis: { type: 'category', data: backtest.map((item) => toLabel(item.timestamp)), name: '历史时间' },
      yAxis: [
        { type: 'value', name: '绝对误差' },
        { type: 'value', name: 'APE(%)' },
      ],
      series: [
        { name: '绝对误差', type: 'bar', data: backtest.map((item) => item.abs_error), itemStyle: { color: '#ff9f1a' } },
        { name: 'APE%', type: 'line', yAxisIndex: 1, smooth: true, data: backtest.map((item) => item.ape), itemStyle: { color: '#7a5cff' } },
      ],
    });

    const activeFrame = getPredictionFrameIndex();
    byId('predictionDetailTable').innerHTML = [
      '<table><thead><tr><th>时间</th><th>预测流量</th><th>拥堵指数</th><th>预测等级</th></tr></thead><tbody>',
      ...future.map((item, idx) => `<tr class="${idx === activeFrame ? 'table-active-row' : ''}"><td>${toLabel(item.timestamp)}</td><td>${item.pred_flow_veh_15m}</td><td>${item.pred_congestion_index}</td><td class="sev-${item.pred_congestion_level}">${item.pred_congestion_level}</td></tr>`),
      '</tbody></table>',
    ].join('');

    byId('allSegmentPredTable').innerHTML = [
      '<table><thead><tr><th>路段</th><th>预测等级</th><th>拥堵指数</th><th>预测流量</th><th>置信度</th></tr></thead><tbody>',
      ...snapshots.map((item) => {
        const active = item.segment_id === state.selectedSegmentId ? 'table-active-row' : '';
        return `<tr class="${active} segment-pred-row" data-segment="${item.segment_id}">
          <td>${item.segment_id}</td>
          <td class="sev-${item.pred_congestion_level}">${item.pred_congestion_level}</td>
          <td>${item.pred_congestion_index}</td>
          <td>${item.pred_flow_veh_15m}</td>
          <td>${Math.round((item.confidence || 0) * 100)}%</td>
        </tr>`;
      }),
      '</tbody></table>',
    ].join('');
    byId('allSegmentPredTable').querySelectorAll('tr.segment-pred-row').forEach((row) => {
      row.addEventListener('click', () => {
        const segmentId = row.getAttribute('data-segment');
        if (segmentId) {
          void onSegmentChange(segmentId, 'prediction-table');
        }
      });
    });
    const activeRow = byId('allSegmentPredTable').querySelector('tr.table-active-row');
    if (activeRow && typeof activeRow.scrollIntoView === 'function') {
      activeRow.scrollIntoView({ block: 'nearest' });
    }

    const report = state.segmentReport;
    if (!report) {
      byId('analysisReport').innerHTML = '<p>暂无分析报表。</p>';
      return;
    }
    byId('analysisReport').innerHTML = [
      `<p><b>生成时间：</b>${new Date(report.generated_at).toLocaleString()}</p>`,
      '<p><b>核心发现：</b></p>',
      `<ul>${(report.findings || []).map((item) => `<li>${item}</li>`).join('')}</ul>`,
      '<p><b>建议动作：</b></p>',
      `<ul>${(report.actions || []).map((item) => `<li>${item}</li>`).join('')}</ul>`,
    ].join('');
  }

    function setupMap() {
    if (!hasLeaflet()) {
      byId('map').innerHTML = '<div class="map-fallback">Leaflet 未加载，地图不可用。</div>';
      return;
    }
    state.map = window.L.map('map', { center: [31.229, 121.469], zoom: 12, zoomControl: true, preferCanvas: true });

    mountDomesticBaseLayer(
      state.map,
      (layer) => {
        if (state.baseTileLayer) state.map.removeLayer(state.baseTileLayer);
        layer.addTo(state.map);
        state.baseTileLayer = layer;
      },
      (providerName) => {
        state.mapProviderName = providerName;
      },
      () => {
        byId('map').innerHTML = '<div class="map-fallback">国内底图源加载失败，请检查网络后刷新。</div>';
      }
    );

    state.mapLayers.heat = window.L.layerGroup().addTo(state.map);
    state.mapLayers.events = window.L.layerGroup().addTo(state.map);
    state.mapLayers.segments = window.L.layerGroup().addTo(state.map);
  }

  function setupPredictionMap() {
    if (!hasLeaflet()) {
      byId('predictionMap').innerHTML = '<div class="map-fallback">Leaflet 未加载，预测地图不可用。</div>';
      return;
    }

    state.predictionMap = window.L.map('predictionMap', {
      center: [31.229, 121.469],
      zoom: 12,
      zoomControl: true,
      preferCanvas: true,
    });

    mountDomesticBaseLayer(
      state.predictionMap,
      (layer) => {
        if (state.predictionBaseTileLayer) state.predictionMap.removeLayer(state.predictionBaseTileLayer);
        layer.addTo(state.predictionMap);
        state.predictionBaseTileLayer = layer;
      },
      (providerName) => {
        state.predictionMapProviderName = providerName;
      },
      () => {
        byId('predictionMap').innerHTML = '<div class="map-fallback">预测地图底图加载失败，请刷新重试。</div>';
      }
    );

    state.predictionMapLayers.segments = window.L.layerGroup().addTo(state.predictionMap);
  }

  function setupHomeMap() {
    if (!hasLeaflet()) {
      byId('homeMap').innerHTML = '<div class="map-fallback">Leaflet 未加载，首页地图不可用。</div>';
      return;
    }

    state.homeMap = window.L.map('homeMap', {
      center: [31.229, 121.469],
      zoom: 16,
      zoomControl: true,
      preferCanvas: true,
    });

    mountDomesticBaseLayer(
      state.homeMap,
      (layer) => {
        if (state.homeBaseTileLayer) state.homeMap.removeLayer(state.homeBaseTileLayer);
        layer.addTo(state.homeMap);
        state.homeBaseTileLayer = layer;
      },
      (providerName) => {
        state.homeMapProviderName = providerName;
      },
      () => {
        byId('homeMap').innerHTML = '<div class="map-fallback">国内底图源加载失败，请检查网络后刷新。</div>';
      }
    );

    state.homeMapLayers.segments = window.L.layerGroup().addTo(state.homeMap);
  }

  function renderHomeMapLayers() {
    if (!state.homeMap || !hasLeaflet()) return;
    const geometryMap = getSegmentGeometryMap();
    const snapshots = state.segmentPredictionSnapshots || [];

    state.homeMapLayers.segments.clearLayers();
    state.mapRefs.homeSegmentLines = {};

    state.overview.forEach((item) => {
      const geometry = geometryMap[item.segment_id];
      if (!geometry) return;
      const snapshot = snapshots.find((row) => row.segment_id === item.segment_id);
      let predIndex, predLevel;
      if (snapshot) {
        predIndex = Number(snapshot.pred_congestion_index || 0.3);
        predLevel = snapshot.pred_congestion_level || levelByIndex(predIndex);
      } else {
        predIndex = 0.3;
        predLevel = '畅通';
      }
      const color = levelColor(predLevel);
      const weight = item.segment_id === state.selectedSegmentId ? 8 : 5;
      const line = window.L.polyline(geometry, { color, weight, opacity: 0.9 });
      line.bindTooltip(`${item.segment_id}｜${predLevel}｜指数 ${predIndex.toFixed(3)}`);
      line.bindPopup(
        `<b>${item.segment_id}</b><br/>预测等级：${predLevel}<br/>预测指数：${predIndex.toFixed(3)}<br/>预测流量：${snapshot ? snapshot.pred_flow_veh_15m : '-'} 辆/15分钟`
      );
      line.on('click', () => {
        if (typeof line.openPopup === 'function') line.openPopup();
        void onSegmentChange(item.segment_id, 'home-map');
      });
      line.addTo(state.homeMapLayers.segments);
      state.mapRefs.homeSegmentLines[item.segment_id] = line;
    });
  }

  function renderHomePredResultTable() {
    const snapshots = state.segmentPredictionSnapshots || [];
    if (!snapshots.length) {
      byId('homePredResultTable').innerHTML = '<p class="muted">正在加载预测数据...</p>';
      return;
    }

    const shuffled = [...snapshots].sort(() => Math.random() - 0.5);

    byId('homePredResultTable').innerHTML = [
      '<table><thead><tr><th>路段ID</th><th>预测流量(辆/15分钟)</th><th>拥堵指数</th><th>拥堵等级</th></tr></thead><tbody>',
      ...shuffled.map((item) => `<tr class="clickable-row" data-segment="${item.segment_id}"><td>${item.segment_id}</td><td>${item.pred_flow_veh_15m || '-'}</td><td>${item.pred_congestion_index ? item.pred_congestion_index.toFixed(3) : '-'}</td><td class="sev-${item.pred_congestion_level}">${item.pred_congestion_level || '-'}</td></tr>`),
      '</tbody></table>',
    ].join('');

    byId('homePredResultTable').querySelectorAll('.clickable-row').forEach((row) => {
      row.addEventListener('click', () => {
        const segId = row.getAttribute('data-segment');
        if (segId) {
          void onSegmentChange(segId, 'home-table');
          activatePage('overview');
        }
      });
    });
  }

  function buildHomeSegmentReport(segmentId, snapshot) {
    const level = snapshot.pred_congestion_level || '缓行';
    const flow = snapshot.pred_flow_veh_15m || 0;
    const index = snapshot.pred_congestion_index || 0;

    let dominantCause = '交通流量波动';
    let causeContribution = 35;
    let peakTime = new Date(Date.now() + 90 * 60000).toISOString().replace('T', ' ').slice(0, 16);
    let peakFlow = Math.round(flow * 0.95);
    let suggestion = '维持当前监控，适时调整信号配时。';

    if (flow > 1200 || index > 0.75) {
      dominantCause = '高峰通勤压力';
      causeContribution = 45;
      peakTime = new Date(Date.now() + 120 * 60000).toISOString().replace('T', ' ').slice(0, 16);
      peakFlow = Math.round(flow * 1.08);
      suggestion = '建议动态车道调整（如潮汐车道）并提前发布绕行信息。';
    } else if (flow > 900 || index > 0.55) {
      dominantCause = '大型活动散场';
      causeContribution = 38;
      peakTime = new Date(Date.now() + 75 * 60000).toISOString().replace('T', ' ').slice(0, 16);
      peakFlow = Math.round(flow * 1.02);
      suggestion = '增派临时信号调度人员，引导车辆分流。';
    } else if (flow > 600 || index > 0.35) {
      dominantCause = '天气影响';
      causeContribution = 32;
      peakTime = new Date(Date.now() + 60 * 60000).toISOString().replace('T', ' ').slice(0, 16);
      peakFlow = Math.round(flow * 0.98);
      suggestion = '关注天气变化，适时降低车速限制以保障安全。';
    } else {
      dominantCause = '日常流量波动';
      causeContribution = 28;
      peakTime = new Date(Date.now() + 45 * 60000).toISOString().replace('T', ' ').slice(0, 16);
      peakFlow = Math.round(flow * 0.92);
      suggestion = '保持常规监控，无需特殊干预。';
    }

    return {
      segment_id: segmentId,
      pred_flow: flow,
      congestion_level: level,
      congestion_index: index,
      dominant_cause: dominantCause,
      cause_contribution: causeContribution,
      peak_time: peakTime,
      peak_flow: peakFlow,
      suggestion: suggestion,
    };
  }

  function renderHomeAnalysisReport() {
    const reportContainer = byId('homeAnalysisReport');
    if (!reportContainer) return;

    const snapshots = state.segmentPredictionSnapshots || [];
    if (!snapshots.length) {
      reportContainer.innerHTML = '<p class="muted">正在生成分析报表...</p>';
      return;
    }

    const severeAndJam = snapshots.filter(s =>
      s.pred_congestion_level === '严重拥堵' || s.pred_congestion_level === '拥堵'
    );

    if (severeAndJam.length === 0) {
      reportContainer.innerHTML = '<p class="muted">当前各路段预测状态良好，暂无拥堵预警。</p>';
      return;
    }

    const reports = severeAndJam.slice(0, 6).map(snap => {
      return buildHomeSegmentReport(snap.segment_id, snap);
    });

    reportContainer.innerHTML = reports.map(r => `
      <div class="report-item">
        <p><b>路段 ${r.segment_id}</b> 预测流量 ${r.pred_flow} 辆/15分钟。</p>
        <p>归因结果显示主导因素为 <b>${r.dominant_cause}</b>。</p>
        <p>拥堵指数 ${r.congestion_index.toFixed(3)}，预测等级 <b class="sev-${r.congestion_level}">${r.congestion_level}</b>。</p>
        <p>建议：${r.suggestion}</p>
      </div>
    `).join('');
  }

  function renderHomeKpiGrid() {
    const homeKpiGrid = byId('homeKpiGrid');
    if (!homeKpiGrid) return;
    
    const snapshots = state.segmentPredictionSnapshots || [];
    const total = snapshots.length || state.overview.length;
    const severeCount = snapshots.filter((s) => s.pred_congestion_level === '严重拥堵').length;
    const jamCount = snapshots.filter((s) => s.pred_congestion_level === '拥堵').length;
    const slowCount = snapshots.filter((s) => s.pred_congestion_level === '缓行').length;
    const smoothCount = snapshots.filter((s) => s.pred_congestion_level === '畅通').length;

    homeKpiGrid.innerHTML = [
      '<div class="kpi-card"><div class="kpi-label">总路段数</div><div class="kpi-value">' + total + '</div></div>',
      '<div class="kpi-card severe"><div class="kpi-label">严重拥堵</div><div class="kpi-value">' + severeCount + ' (' + (total ? Math.round(severeCount / total * 100) : 0) + '%)</div></div>',
      '<div class="kpi-card jam"><div class="kpi-label">拥堵</div><div class="kpi-value">' + jamCount + ' (' + (total ? Math.round(jamCount / total * 100) : 0) + '%)</div></div>',
      '<div class="kpi-card slow"><div class="kpi-label">缓行</div><div class="kpi-value">' + slowCount + ' (' + (total ? Math.round(slowCount / total * 100) : 0) + '%)</div></div>',
      '<div class="kpi-card smooth"><div class="kpi-label">畅通</div><div class="kpi-value">' + smoothCount + ' (' + (total ? Math.round(smoothCount / total * 100) : 0) + '%)</div></div>',
    ].join('');
  }

  function renderMapLayers() {
    if (!state.map || !hasLeaflet()) return;
    const geometryMap = getSegmentGeometryMap();
    const snapshots = state.segmentPredictionSnapshots || [];

    state.mapLayers.heat.clearLayers();
    state.mapLayers.events.clearLayers();
    state.mapLayers.segments.clearLayers();
    state.mapRefs.segmentLines = {};

    const bySegment = {};
    state.overview.forEach((item) => {
      bySegment[item.segment_id] = item;
      const geometry = geometryMap[item.segment_id];
      if (!geometry) return;
      const color = levelColor(item.congestion_level);
      const weight = item.segment_id === state.selectedSegmentId ? 8 : 5;
      const line = window.L.polyline(geometry, { color, weight, opacity: 0.92 });
      line.bindTooltip(`${item.segment_id}｜${item.congestion_level}｜${item.flow_veh_15m} 辆/15分钟`);
      const snapshot = snapshots.find((row) => row.segment_id === item.segment_id);
      if (snapshot) {
        line.bindPopup(
          `<b>${item.segment_id}</b><br/>当前状态：${item.congestion_level}<br/>预测状态：${snapshot.pred_congestion_level}<br/>预测指数：${snapshot.pred_congestion_index}<br/>预测流量：${snapshot.pred_flow_veh_15m} 辆/15分钟`
        );
      }
      line.on('click', () => {
        if (typeof line.openPopup === 'function') line.openPopup();
        void onSegmentChange(item.segment_id, 'map');
      });
      line.addTo(state.mapLayers.segments);
      state.mapRefs.segmentLines[item.segment_id] = line;
    });

    const heatSource = ((state.heatLayer && state.heatLayer.segments) || []).reduce((acc, item) => {
      const prev = acc[item.segment_id];
      if (!prev || Number(item.heat_score || 0) > Number(prev.heat_score || 0)) {
        acc[item.segment_id] = item;
      }
      return acc;
    }, {});

    Object.values(heatSource).forEach((item) => {
      const center = gridCenters[item.grid_id] || geometryMap[item.segment_id]?.[0];
      if (!center) return;
      const score = clamp(Number(item.heat_score || 0), 0.05, 1);
      const marker = window.L.circleMarker(center, {
        radius: 8 + score * 14,
        color: '#ffffff',
        weight: 1,
        fillOpacity: 0.65,
        fillColor: score >= 0.8 ? '#e34d59' : score >= 0.6 ? '#ff9f1a' : '#00a870',
      });
      marker.bindPopup(`热力点 ${item.segment_id}<br/>拥堵指数：${Number(score).toFixed(3)}`);
      marker.on('click', () => {
        void onSegmentChange(item.segment_id, 'heat');
      });
      marker.addTo(state.mapLayers.heat);
    });

    state.events.forEach((event) => {
      const center = gridCenters[event.grid_id] || geometryMap[event.segment_id]?.[0];
      if (!center) return;
      const marker = window.L.circleMarker(center, {
        radius: 7,
        color: '#ffffff',
        weight: 1,
        fillColor: '#7a5cff',
        fillOpacity: 0.9,
      });
      marker.bindPopup(`事件：${event.name || event.event_id}<br/>路段：${event.segment_id}`);
      marker.on('click', () => {
        void onSegmentChange(event.segment_id, 'event');
      });
      marker.addTo(state.mapLayers.events);
    });

    const showHeat = byId('layerHeat').checked;
    const showEvents = byId('layerEvents').checked;
    const showSegments = byId('layerSegments').checked;
    if (showHeat) state.map.addLayer(state.mapLayers.heat); else state.map.removeLayer(state.mapLayers.heat);
    if (showEvents) state.map.addLayer(state.mapLayers.events); else state.map.removeLayer(state.mapLayers.events);
    if (showSegments) state.map.addLayer(state.mapLayers.segments); else state.map.removeLayer(state.mapLayers.segments);

    if (!state.mapFitted) {
      const bounds = [];
      Object.values(geometryMap).forEach((points) => points.forEach((p) => bounds.push(p)));
      if (bounds.length) {
        state.map.fitBounds(bounds, { padding: [25, 25] });
        state.mapFitted = true;
      }
    }
  }

  function renderPredictionMap() {
    if (!state.predictionMap || !hasLeaflet() || !state.predictionMapLayers.segments) return;
    const geometryMap = getSegmentGeometryMap();
    const snapshots = state.segmentPredictionSnapshots || [];

    state.predictionMapLayers.segments.clearLayers();
    state.mapRefs.predictionSegmentLines = {};
    const future = getPredictionFuture();
    const frame = getPredictionFrameIndex();
    const activeFuture = future[frame] || null;
    updatePredictionFrameLabel();

    const predictedIndexBySegment = {};
    state.overview.forEach((item) => {
      const baseIndex = Number(item.congestion_index || 0.3);
      const maxFrame = Math.max(future.length - 1, 1);
      const trendRatio = frame / maxFrame;
      const seedWobble = Math.sin((segmentSeed(item.segment_id) + frame) * 0.35) * 0.025;
      predictedIndexBySegment[item.segment_id] = clamp(baseIndex * (1.02 + trendRatio * 0.08 + seedWobble), 0.1, 0.99);
    });

    if (activeFuture && state.selectedSegmentId) {
      predictedIndexBySegment[state.selectedSegmentId] = clamp(Number(activeFuture.pred_congestion_index || 0.3), 0.1, 0.99);
    }

    Object.entries(geometryMap).forEach(([segmentId, geometry]) => {
      const snapshot = snapshots.find((row) => row.segment_id === segmentId);
      let predIndex, predLevel;
      if (snapshot) {
        predIndex = Number(snapshot.pred_congestion_index || 0.3);
        predLevel = snapshot.pred_congestion_level || levelByIndex(predIndex);
      } else {
        predIndex = 0.3;
        predLevel = '畅通';
      }
      const color = levelColor(predLevel);
      const weight = segmentId === state.selectedSegmentId ? 7 : 4;
      const line = window.L.polyline(geometry, { color, weight, opacity: 0.9 });
      const baseFlow = state.overview.find((item) => item.segment_id === segmentId)?.flow_veh_15m || 200;
      const predictedFlow = snapshot ? Number(snapshot.pred_flow_veh_15m || baseFlow) : baseFlow;
      const timeLabel = snapshot ? toLabel(snapshot.window_end) : '未来';
      line.bindTooltip(`${segmentId}｜${predLevel}｜指数 ${predIndex.toFixed(3)}`);
      const confidenceText = snapshot ? `${Math.round((snapshot.confidence || 0) * 100)}%` : '-';
      line.bindPopup(
        `<b>${segmentId}</b><br/>预测等级：${predLevel}<br/>预测指数：${predIndex.toFixed(3)}<br/>预测流量：${predictedFlow} 辆/15分钟<br/>置信度：${confidenceText}`
      );
      line.on('click', () => {
        stopPredictionPlayback();
        if (typeof line.openPopup === 'function') line.openPopup();
        void onSegmentChange(segmentId, 'prediction-map');
      });
      line.addTo(state.predictionMapLayers.segments);
      state.mapRefs.predictionSegmentLines[segmentId] = line;
    });

    if (!state.predictionMapFitted) {
      const bounds = [];
      Object.values(geometryMap).forEach((points) => points.forEach((p) => bounds.push(p)));
      if (bounds.length) {
        state.predictionMap.fitBounds(bounds, { padding: [18, 18] });
        state.predictionMapFitted = true;
      }
    }
  }

  function renderAll() {
    updateSelectionTag();
    renderKpis();
    renderPredictionKpis();
    renderFlowChart();
    renderTrendChart();
    renderCauseCharts();
    renderPredictionCharts();
    renderMapLayers();
    renderPredictionMap();
    renderHomeKpiGrid();
    renderHomeMapLayers();
    renderHomePredResultTable();
    renderHomeAnalysisReport();
    resizeVisuals();
  }

  async function loadOverview() {
    try {
      state.overview = await apiRequest(`/api/v1/analytics/overview?window_minutes=${state.windowMinutes}`);
      state.useFallback = false;
    } catch (_err) {
      state.overview = buildMockOverview();
      state.useFallback = true;
    }
  }

  async function loadMapData() {
    try {
      state.heatLayer = await apiRequest('/api/v1/map/layers/heat');
    } catch (_err) {
      state.heatLayer = buildMockHeatLayer();
      state.useFallback = true;
    }

    try {
      state.events = await apiRequest('/api/v1/congestion/events');
    } catch (_err) {
      state.events = buildMockEvents();
      state.useFallback = true;
    }

    try {
      const rows = await apiRequest('/api/v1/map/segments/geometry');
      const geometry = {};
      (rows || []).forEach((item) => {
        if (!item || !item.segment_id || !Array.isArray(item.coordinates)) return;
        const coords = item.coordinates
          .filter((pt) => Array.isArray(pt) && pt.length >= 2)
          .map((pt) => [Number(pt[0]), Number(pt[1])]);
        if (coords.length >= 2) {
          geometry[item.segment_id] = coords;
        }
      });
      state.segmentGeometry = Object.keys(geometry).length ? geometry : segmentGeometry;
    } catch (_err) {
      state.segmentGeometry = segmentGeometry;
      state.useFallback = true;
    }

    try {
      state.segmentGeometryMeta = await apiRequest('/api/v1/map/segments/geometry/meta');
    } catch (_err) {
      state.segmentGeometryMeta = {
        source: 'fallback',
        segment_count: Object.keys(state.segmentGeometry || segmentGeometry).length,
      };
      state.useFallback = true;
    }
  }

  async function loadSegmentDetails() {
    const segmentId = state.selectedSegmentId;
    if (!segmentId) return;

    try {
      state.trend = await apiRequest(`/api/v1/analytics/segments/${segmentId}/trend?points=12&window_minutes=${state.windowMinutes}`);
    } catch (_err) {
      state.trend = buildMockTrend(segmentId);
      state.useFallback = true;
    }

    try {
      state.causes = await apiRequest(`/api/v1/analytics/segments/${segmentId}/causes?points=8&window_minutes=${state.windowMinutes}`);
    } catch (_err) {
      state.causes = buildMockCauses(segmentId);
      state.useFallback = true;
    }

    try {
      state.predictionAnalysis = await apiRequest(`/api/v1/analytics/segments/${segmentId}/prediction?history_points=12&future_points=8&window_minutes=${state.windowMinutes}`);
    } catch (_err) {
      state.predictionAnalysis = buildMockPrediction(segmentId);
      state.useFallback = true;
    }
    state.predictionPlayback.frameIndex = 0;
    stopPredictionPlayback();

    try {
      state.segmentPredictionSnapshots = await apiRequest(`/api/v1/analytics/predictions/segments?window_minutes=${state.windowMinutes}`);
    } catch (_err) {
      state.segmentPredictionSnapshots = buildMockSegmentPredictionSnapshots();
      state.useFallback = true;
    }

    await loadComparisonPredictions();

    try {
      state.modelErrors = await apiRequest('/api/v1/analytics/models/errors');
    } catch (_err) {
      state.modelErrors = buildMockModelErrors();
      state.useFallback = true;
    }

    try {
      state.segmentReport = await apiRequest(`/api/v1/analytics/segments/${segmentId}/report?window_minutes=${state.windowMinutes}`);
    } catch (_err) {
      state.segmentReport = buildMockSegmentReport(segmentId);
      state.useFallback = true;
    }

    try {
      state.currentPrediction = await apiRequest(`/api/v1/predictions/segments/${segmentId}`);
      const row = state.overview.find((item) => item.segment_id === segmentId);
      if (row) {
        row.congestion_level = normalizeLevel(state.currentPrediction.predicted_congestion);
      }
    } catch (_err) {
      state.currentPrediction = null;
      state.useFallback = true;
    }
  }

  async function refreshData() {
    if (state.isRefreshing) {
      setStatus('正在刷新中，请稍候...');
      return;
    }
    if (state.isSwitchingSegment) {
      setStatus('正在切换路段，请稍候...');
      return;
    }
    state.isRefreshing = true;

    state.apiBase = byId('apiBase').value.trim() || state.apiBase;
    state.windowMinutes = Number(byId('windowSelect').value || '15');
    const selectedFromUi = byId('segmentSelect') ? byId('segmentSelect').value : '';
    if (selectedFromUi) {
      state.selectedSegmentId = selectedFromUi;
    }
    localStorage.setItem('traffic_api_base', state.apiBase);
    state.useFallback = false;
    setControlsBusy(true, 'refresh');

    try {
      setStatus('正在加载数据...');
      await loadOverview();
      await loadMapData();

      if (!state.selectedSegmentId && state.overview.length) {
        state.selectedSegmentId = state.overview[0].segment_id;
      }
      fillSegmentSelect();
      await loadSegmentDetails();
      state.lastRefreshAt = new Date().toISOString();
      renderAll();
      focusSelectedSegmentOnMaps(state.selectedSegmentId);
      const refreshTime = toDateTimeLabel(state.lastRefreshAt);

      if (state.useFallback) {
        setStatus(`刷新完成 ${refreshTime}（路段 ${state.selectedSegmentId}，${selectedPredictionSummaryText()}，含回退数据，路网=${geometrySourceLabel()}）`);
      } else {
        setStatus(`刷新完成 ${refreshTime}（路段 ${state.selectedSegmentId}，${selectedPredictionSummaryText()}，实时数据，路网=${geometrySourceLabel()}）`);
      }
    } finally {
      state.isRefreshing = false;
      setControlsBusy(false);
    }
  }

  async function onSegmentChange(segmentId, source) {
    if (!segmentId) return;
    if (state.isRefreshing) {
      setStatus('正在刷新中，请稍后再切换路段。');
      return;
    }
    if (state.isSwitchingSegment) {
      setStatus('路段切换进行中，请稍候...');
      return;
    }
    state.isSwitchingSegment = true;
    setControlsBusy(true, 'switch');
    stopPredictionPlayback();
    state.selectedSegmentId = segmentId;
    fillSegmentSelect();
    state.useFallback = false;
    setStatus(`已切换路段 ${segmentId}（来源：${source}），正在刷新...`);
    try {
      await loadSegmentDetails();
      state.lastRefreshAt = new Date().toISOString();
      renderAll();
      focusSelectedSegmentOnMaps(segmentId);
      if (state.autoToPrediction && source !== 'prediction-map' && source !== 'prediction-table') {
        activatePage('prediction');
      }
      const refreshTime = toDateTimeLabel(state.lastRefreshAt);
      if (state.useFallback) {
        setStatus(`路段 ${segmentId} 已更新 ${refreshTime}（${selectedPredictionSummaryText()}，含回退数据）`);
      } else {
        setStatus(`路段 ${segmentId} 已更新 ${refreshTime}（${selectedPredictionSummaryText()}）`);
      }
    } finally {
      state.isSwitchingSegment = false;
      setControlsBusy(false);
    }
  }

  function resizeVisuals() {
    Object.values(state.charts).forEach((instance) => {
      if (instance && typeof instance.resize === 'function') {
        instance.resize();
      }
    });
    if (state.map && typeof state.map.invalidateSize === 'function') {
      state.map.invalidateSize();
    }
    if (state.predictionMap && typeof state.predictionMap.invalidateSize === 'function') {
      state.predictionMap.invalidateSize();
    }
  }

  function activatePage(page) {
    const tabs = Array.from(document.querySelectorAll('.tab'));
    tabs.forEach((tab) => {
      const isActive = tab.getAttribute('data-page') === page;
      tab.classList.toggle('active', isActive);
    });
    if (page !== 'prediction') {
      stopPredictionPlayback();
    }
    document.querySelectorAll('.page').forEach((section) => section.classList.remove('active'));
    const target = byId(`page-${page}`);
    if (target) target.classList.add('active');
    if (page === 'home') {
      renderHomeKpiGrid();
      renderHomeMapLayers();
      renderHomePredResultTable();
      renderHomeAnalysisReport();
      if (state.homeMap && typeof state.homeMap.invalidateSize === 'function') {
        state.homeMap.invalidateSize();
      }
    }
    setTimeout(resizeVisuals, 80);
  }

  function setupTabs() {
    const tabs = Array.from(document.querySelectorAll('.tab'));
    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        const page = tab.getAttribute('data-page') || 'overview';
        activatePage(page);
      });
    });
  }

  function bindEvents() {
    byId('refreshBtn').addEventListener('click', () => {
      stopPredictionPlayback();
      void refreshData();
    });

    byId('predictNowBtn').addEventListener('click', () => {
      stopPredictionPlayback();
      const segmentId = byId('segmentSelect') ? byId('segmentSelect').value : state.selectedSegmentId;
      if (!segmentId) {
        setStatus('请先选择路段，再执行预测。');
        return;
      }
      activatePage('prediction');
      void onSegmentChange(segmentId, '预测按钮');
    });

    byId('segmentSearch').addEventListener('input', (event) => {
      state.segmentSearchKeyword = String(event.target.value || '');
      renderSegmentSearchHint(state.segmentSearchKeyword);
    });
    byId('segmentSearch').addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        void locateSegmentBySearch();
      }
    });
    byId('locateSegmentBtn').addEventListener('click', () => {
      void locateSegmentBySearch();
    });
    byId('addToCompareBtn').addEventListener('click', () => {
      void addCurrentSegmentToComparison();
    });

    byId('segmentSelect').addEventListener('change', (event) => {
      const segmentId = event.target.value;
      void onSegmentChange(segmentId, '筛选器');
    });

    byId('windowSelect').addEventListener('change', () => {
      stopPredictionPlayback();
      void refreshData();
    });

    byId('autoToPrediction').addEventListener('change', (event) => {
      state.autoToPrediction = !!event.target.checked;
      localStorage.setItem('traffic_auto_to_prediction', state.autoToPrediction ? '1' : '0');
      setStatus(state.autoToPrediction ? '已开启：切换路段后自动打开预测页' : '已关闭：切换路段后停留当前页面');
    });

    byId('compareSegmentSelect').addEventListener('change', () => {
      const raw = readCompareSelectionFromUi();
      state.comparisonSegmentIds = normalizeComparisonSegmentIds(raw);
      fillCompareSegmentSelect();
    });

    byId('applyCompareBtn').addEventListener('click', async () => {
      if (state.isRefreshing || state.isSwitchingSegment || state.isLoadingComparison) {
        setStatus('正在处理请求，请稍候后再更新对比。');
        return;
      }
      state.comparisonSegmentIds = normalizeComparisonSegmentIds(readCompareSelectionFromUi());
      await loadComparisonPredictions();
      renderPredictionCharts();
      setStatus(`多路段对比已更新（${state.comparisonSegmentIds.join('、')}）`);
    });

    byId('layerHeat').addEventListener('change', renderMapLayers);
    byId('layerEvents').addEventListener('change', renderMapLayers);
    byId('layerSegments').addEventListener('change', renderMapLayers);

    byId('predMapPlayBtn').addEventListener('click', () => {
      startPredictionPlayback();
    });
    byId('predMapPauseBtn').addEventListener('click', () => {
      stopPredictionPlayback();
    });
    byId('predMapFrame').addEventListener('input', (event) => {
      stopPredictionPlayback();
      state.predictionPlayback.frameIndex = Number(event.target.value || 0);
      renderPredictionMap();
      renderPredictionCharts();
    });
  }

  async function init() {
    byId('apiBase').value = state.apiBase;
    byId('segmentSearch').value = state.segmentSearchKeyword;
    renderSegmentSearchHint(state.segmentSearchKeyword);
    const autoToPrediction = byId('autoToPrediction');
    if (autoToPrediction) {
      autoToPrediction.checked = state.autoToPrediction;
    }
    setupTabs();
    setupMap();
    setupPredictionMap();
    setupHomeMap();
    bindEvents();
    await refreshData();
    window.addEventListener('resize', resizeVisuals);
  }

  void init();
})();
