/* Chart.js helpers — 레퍼런스 스타일 (도넛 중앙텍스트 / 막대 값라벨 / 그라데이션) */
Chart.defaults.font.family = "'Malgun Gothic','맑은 고딕',sans-serif";
Chart.defaults.color = '#5b6678';
Chart.defaults.animation = false;
Chart.defaults.animations = false;

var PALETTE = ['#2f6fed', '#27ae60', '#e08e2a', '#8b5cf6', '#e0533f',
               '#16b5c4', '#64748b', '#b8902f'];

function gradH(_id, c1, c2) {
  return function (ctx) {
    var ch = ctx.chart, a = ch.chartArea; if (!a) return c1;
    var g = ch.ctx.createLinearGradient(a.left, 0, a.right, 0);
    g.addColorStop(0, c1); g.addColorStop(1, c2); return g;
  };
}
function gradV(_id, c1, c2) {
  return function (ctx) {
    var ch = ctx.chart, a = ch.chartArea; if (!a) return c2;
    var g = ch.ctx.createLinearGradient(0, a.bottom, 0, a.top);
    g.addColorStop(0, c1); g.addColorStop(1, c2); return g;
  };
}
function hourColors(arr, peak) {
  return arr.map(function (v, i) {
    if (i === peak) return '#e0533f';
    if (v >= peak * 0.6) return '#e08e2a';
    return '#3f7bf0';
  });
}

/* 막대 끝/위에 값 라벨 */
var valueLabel = {
  id: 'valueLabel',
  afterDatasetsDraw: function (chart) {
    if (chart.config.type !== 'bar') return;
    var horiz = chart.options.indexAxis === 'y';
    var ctx = chart.ctx;
    chart.data.datasets.forEach(function (ds, di) {
      var meta = chart.getDatasetMeta(di);
      meta.data.forEach(function (el, i) {
        var v = ds.data[i]; if (v == null) return;
        ctx.save();
        ctx.fillStyle = '#33414f';
        ctx.font = '700 10.5px Malgun Gothic';
        if (horiz) { ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
          ctx.fillText(v.toLocaleString(), el.x + 6, el.y); }
        else { ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
          ctx.fillText(v.toLocaleString(), el.x, el.y - 4); }
        ctx.restore();
      });
    });
  }
};

/* 도넛 중앙 텍스트 */
var centerText = {
  id: 'centerText',
  afterDraw: function (chart) {
    var c = chart.options.__center; if (!c) return;
    var a = chart.chartArea, ctx = chart.ctx;
    var cx = (a.left + a.right) / 2, cy = (a.top + a.bottom) / 2;
    ctx.save(); ctx.textAlign = 'center';
    ctx.fillStyle = '#1b2940'; ctx.font = '800 26px Malgun Gothic';
    ctx.textBaseline = 'bottom'; ctx.fillText(c.text, cx, cy + 6);
    ctx.fillStyle = '#8a93a3'; ctx.font = '600 12px Malgun Gothic';
    ctx.textBaseline = 'top'; ctx.fillText(c.unit, cx, cy + 8);
    ctx.restore();
  }
};
Chart.register(valueLabel, centerText);

function hbarOpts() {
  return {
    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
    layout: { padding: { right: 34, left: 4 } },
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
    scales: {
      x: { beginAtZero: true, grid: { color: '#eef1f6' }, border: { display: false },
           ticks: { font: { size: 10 }, color: '#9aa3b1' } },
      y: { grid: { display: false }, border: { display: false },
           ticks: { font: { size: 11 }, color: '#3b4757' } }
    }
  };
}
function vbarOpts() {
  return {
    responsive: true, maintainAspectRatio: false,
    layout: { padding: { top: 18 } },
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
    scales: {
      x: { grid: { display: false }, border: { display: false },
           ticks: { font: { size: 9.5 }, color: '#6b7686', maxRotation: 45, minRotation: 0 } },
      y: { beginAtZero: true, grid: { color: '#eef1f6', borderDash: [3, 3] }, border: { display: false },
           ticks: { font: { size: 10 }, color: '#9aa3b1' } }
    }
  };
}
function donutOpts(centerVal, unit) {
  return {
    responsive: true, maintainAspectRatio: false, cutout: '62%',
    layout: { padding: 6 },
    plugins: {
      legend: { position: 'bottom', labels: { boxWidth: 11, boxHeight: 11, padding: 12, font: { size: 11 }, color: '#475569' } },
      tooltip: { enabled: false }
    },
    __center: { text: centerVal, unit: unit }
  };
}

function lineOpts() {
  return {
    responsive: true, maintainAspectRatio: false,
    layout: { padding: { top: 14, right: 12 } },
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
    scales: {
      x: { grid: { display: false }, border: { display: false }, ticks: { font: { size: 10 }, color: '#6b7686' } },
      y: { beginAtZero: true, grid: { color: '#eef1f6', borderDash: [3, 3] }, border: { display: false },
           ticks: { font: { size: 10 }, color: '#9aa3b1' } }
    }
  };
}

function makeChart(id, cfg) {
  var el = document.getElementById(id); if (!el) return;
  new Chart(el, cfg);
}
