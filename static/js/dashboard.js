/**
 * dashboard.js
 * Fetches analytics from Flask API and renders all Chart.js charts.
 * Populates KPI cards, insights, and sustainability score.
 */

// ── Chart.js global defaults ──────────────────────────────────────────────
Chart.defaults.color = 'rgba(255,255,255,0.5)';
Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family = "'DM Sans', sans-serif";
Chart.defaults.font.size = 11;

// ── Helpers ───────────────────────────────────────────────────────────────

/** Format large numbers: 4200 → "4,200" */
function fmt(n) {
  if (n === undefined || n === null) return '—';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000)     return n.toLocaleString('en-US', { maximumFractionDigits: 0 });
  return n.toFixed(1);
}

/** Return trend arrow HTML with correct colour class */
function trendHTML(val) {
  if (val === 0) return `<span class="trend-flat">→ Stable</span>`;
  const cls  = val > 0 ? 'trend-up'   : 'trend-down';
  const icon = val > 0 ? '↑'          : '↓';
  const sign = val > 0 ? '+'          : '';
  return `<span class="${cls}">${icon} ${sign}${val}% vs previous period</span>`;
}

/** Determine score colour */
function scoreColor(s) {
  if (s >= 75) return '#10b981';
  if (s >= 50) return '#f59e0b';
  return '#ef4444';
}

/** Determine score status text + class */
function scoreStatus(s) {
  if (s >= 75) return { text: '✅ Excellent',  cls: 'status-good' };
  if (s >= 50) return { text: '⚠️ Moderate',  cls: 'status-medium' };
  return              { text: '🔴 Needs Work', cls: 'status-poor' };
}

// ── Chart instances (kept so they can be destroyed on re-render) ──────────
let charts = {};

function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

// ═══════════════════════════════════════════════════════════════════════════
//  RENDER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

function renderKPIs(d) {
  document.getElementById('kpiEnergy').textContent      = fmt(d.total_energy)  + ' kWh';
  document.getElementById('kpiWater').textContent       = fmt(d.total_water)   + ' L';
  document.getElementById('kpiWaste').textContent       = fmt(d.total_waste)   + ' kg';
  document.getElementById('kpiScore').textContent       = d.efficiency_score   + '/100';

  document.getElementById('kpiEnergyTrend').innerHTML   = trendHTML(d.energy_trend);
  document.getElementById('kpiWaterTrend').innerHTML    = trendHTML(d.water_trend);
  document.getElementById('kpiWasteTrend').innerHTML    = trendHTML(d.waste_trend);
  document.getElementById('kpiScoreTrend').innerHTML    = `<span class="trend-flat">Based on dataset analysis</span>`;

  document.getElementById('metaText').textContent =
    `${d.row_count} records analysed`;
}


function renderEnergyChart(d) {
  destroyChart('energy');
  const ctx = document.getElementById('energyChart').getContext('2d');

  // Gradient fill
  const grad = ctx.createLinearGradient(0, 0, 0, 200);
  grad.addColorStop(0, 'rgba(30,95,196,0.4)');
  grad.addColorStop(1, 'rgba(30,95,196,0)');

  charts.energy = new Chart(ctx, {
    type: 'line',
    data: {
      labels: d.energy_labels,
      datasets: [{
        label: 'Energy (kWh)',
        data: d.energy_values,
        borderColor: '#4a90e2',
        backgroundColor: grad,
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: '#4a90e2',
        fill: true,
        tension: 0.4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(13,27,42,0.95)',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          titleColor: 'rgba(255,255,255,0.9)',
          bodyColor: 'rgba(255,255,255,0.6)',
          padding: 10,
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { maxTicksLimit: 8 }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { callback: v => v.toLocaleString() }
        }
      }
    }
  });
}


function renderWasteChart(d) {
  destroyChart('waste');
  const ctx = document.getElementById('wasteChart').getContext('2d');

  charts.waste = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Recycled', 'Landfill', 'Compost'],
      datasets: [{
        data: d.waste_breakdown,
        backgroundColor: ['#10b981', '#ef4444', '#f59e0b'],
        borderColor: 'rgba(13,27,42,0.8)',
        borderWidth: 3,
        hoverOffset: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 12,
            usePointStyle: true,
            pointStyleWidth: 8,
          }
        },
        tooltip: {
          backgroundColor: 'rgba(13,27,42,0.95)',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
        }
      }
    }
  });
}


function renderScoreChart(score) {
  destroyChart('score');
  const ctx = document.getElementById('scoreChart').getContext('2d');
  const col = scoreColor(score);

  charts.score = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [score, 100 - score],
        backgroundColor: [col, 'rgba(255,255,255,0.06)'],
        borderWidth: 0,
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '78%',
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      animation: { animateRotate: true, duration: 1200 }
    }
  });

  // Update DOM
  const el = document.getElementById('scoreNumber');
  el.textContent = score;
  el.style.color = col;

  const status = scoreStatus(score);
  const statusEl = document.getElementById('scoreStatus');
  statusEl.textContent = status.text;
  statusEl.className   = 'score-status ' + status.cls;
}


function renderDeptChart(d) {
  destroyChart('dept');
  const ctx = document.getElementById('deptChart').getContext('2d');

  charts.dept = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: d.dept_labels,
      datasets: [{
        label: 'Water (L)',
        data: d.dept_water,
        backgroundColor: 'rgba(0,229,192,0.3)',
        borderColor: '#00e5c0',
        borderWidth: 1.5,
        borderRadius: 5,
        hoverBackgroundColor: 'rgba(0,229,192,0.5)',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: d.dept_labels.length > 5 ? 'y' : 'x',  // flip to horizontal if many depts
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(13,27,42,0.95)',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
        }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' } },
        y: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { callback: v => v.toLocaleString() }
        }
      }
    }
  });
}


function renderInsights(insights) {
  const ul = document.getElementById('insightsList');
  ul.innerHTML = insights
    .map(i => `<li>${i}</li>`)
    .join('');
}


// ═══════════════════════════════════════════════════════════════════════════
//  MAIN — Fetch data and render everything
// ═══════════════════════════════════════════════════════════════════════════

async function loadDashboard() {
  try {
    const res  = await fetch(`/api/analytics?filename=${encodeURIComponent(FILENAME)}`);
    const data = await res.json();

    if (data.error) {
      alert('Error processing data: ' + data.error);
      return;
    }

    // Render all sections
    renderKPIs(data);
    renderEnergyChart(data);
    renderWasteChart(data);
    renderScoreChart(data.sustainability_score);
    renderDeptChart(data);
    renderInsights(data.insights);

    // Hide loading overlay
    document.getElementById('loadingOverlay').style.display = 'none';

  } catch (err) {
    console.error('Dashboard load error:', err);
    document.getElementById('loadingOverlay').innerHTML =
      `<p style="color:#ef4444">Failed to load dashboard. <a href="/" style="color:#00e5c0">Go back</a></p>`;
  }
}

// ── Sidebar active link tracking ──────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(link => {
  link.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(l => l.classList.remove('active'));
    link.classList.add('active');
  });
});

// ═══════════════════════════════════════════════════════════════════════════
//  AI DASHBOARD — Fetch + Render all AI panels
// ═══════════════════════════════════════════════════════════════════════════

async function loadAIDashboard() {
  try {
    const res  = await fetch(`/api/ai?filename=${encodeURIComponent(FILENAME)}`);
    const data = await res.json();

    if (data.error) {
      console.warn('AI error:', data.error);
      return;
    }

    renderAnomalies(data.anomalies);
    renderRootCause(data.root_cause);
    renderDeptContrib(data.root_cause);
    renderRecommendations(data.recommendations);
    renderPrediction(data.predictions);

  } catch (err) {
    console.error('AI load error:', err);
  }
}


// ── Anomaly Cards ─────────────────────────────────────────────────────────
function renderAnomalies(anomalies) {
  const grid = document.getElementById('anomalyGrid');

  if (!anomalies || anomalies.length === 0) {
    grid.innerHTML = `<div class="ai-loading">✅ No anomalies detected — all resources within normal range.</div>`;
    return;
  }

  grid.innerHTML = anomalies.map((a, i) => `
    <div class="anomaly-card ${a.severity}" style="animation-delay:${i * 0.08}s">
      <div class="anomaly-top">
        <span class="anomaly-badge badge-${a.severity}">${a.severity}</span>
        <span class="anomaly-date">${a.date}</span>
      </div>
      <div class="anomaly-msg">
        ${a.direction === 'above' ? '⬆️' : '⬇️'} ${a.resource} usage ${a.direction} average
      </div>
      <div class="anomaly-dev">
        ${a.value} vs avg ${a.avg} &nbsp;|&nbsp; <strong style="color:${a.severity === 'critical' ? '#ef4444' : '#f59e0b'}">${a.deviation}% deviation</strong>
      </div>
    </div>
  `).join('');
}


// ── Root Cause Chart ──────────────────────────────────────────────────────
function renderRootCause(rootCause) {
  destroyChart('rootCause');
  if (!rootCause || !rootCause.factors) return;

  const ctx = document.getElementById('rootCauseChart').getContext('2d');
  const factors = rootCause.factors;

  charts.rootCause = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: factors.map(f => f.label),
      datasets: [{
        label: 'Contribution %',
        data: factors.map(f => f.value),
        backgroundColor: ['rgba(239,68,68,0.5)', 'rgba(245,158,11,0.5)', 'rgba(30,95,196,0.5)', 'rgba(16,185,129,0.5)'],
        borderColor:     ['#ef4444', '#f59e0b', '#1e5fc4', '#10b981'],
        borderWidth: 1.5,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(13,27,42,0.95)',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          callbacks: { label: ctx => ` ${ctx.raw}% contribution` }
        }
      },
      scales: {
        x: {
          max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { callback: v => v + '%' }
        },
        y: { grid: { display: false } }
      }
    }
  });
}


// ── Dept Energy Contribution Doughnut ────────────────────────────────────
function renderDeptContrib(rootCause) {
  destroyChart('deptContrib');
  if (!rootCause || !rootCause.dept_contributions) return;

  const ctx  = document.getElementById('deptContribChart').getContext('2d');
  const dc   = rootCause.dept_contributions;
  const colors = ['#ef4444','#f59e0b','#10b981','#1e5fc4','#8b5cf6','#00e5c0'];

  charts.deptContrib = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: dc.labels,
      datasets: [{
        data: dc.values,
        backgroundColor: colors.slice(0, dc.labels.length).map(c => c + 'cc'),
        borderColor: colors.slice(0, dc.labels.length),
        borderWidth: 2,
        hoverOffset: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '60%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { padding: 10, usePointStyle: true, pointStyleWidth: 8 }
        },
        tooltip: {
          backgroundColor: 'rgba(13,27,42,0.95)',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw}%` }
        }
      }
    }
  });
}


// ── Recommendations ───────────────────────────────────────────────────────
function renderRecommendations(recs) {
  const grid = document.getElementById('recGrid');

  if (!recs || recs.length === 0) {
    grid.innerHTML = `<div class="ai-loading">No recommendations generated.</div>`;
    return;
  }

  grid.innerHTML = recs.map((r, i) => `
    <div class="rec-card" style="animation-delay:${i * 0.1}s">
      <div class="rec-top">
        <span class="rec-icon">${r.icon}</span>
        <span class="priority-badge priority-${r.priority}">${r.priority}</span>
      </div>
      <div class="rec-title">${r.title}</div>
      <div class="rec-desc">${r.description}</div>
      <div class="rec-saving">💰 ${r.saving}</div>
    </div>
  `).join('');
}


// ── Prediction Chart ──────────────────────────────────────────────────────
function renderPrediction(pred) {
  destroyChart('prediction');
  if (!pred || !pred.hist_labels) return;

  const ctx = document.getElementById('predictionChart').getContext('2d');

  // Gradient for historical
  const gradHist = ctx.createLinearGradient(0, 0, 0, 240);
  gradHist.addColorStop(0, 'rgba(74,144,226,0.3)');
  gradHist.addColorStop(1, 'rgba(74,144,226,0)');

  // Gradient for predicted
  const gradPred = ctx.createLinearGradient(0, 0, 0, 240);
  gradPred.addColorStop(0, 'rgba(0,229,192,0.25)');
  gradPred.addColorStop(1, 'rgba(0,229,192,0)');

  const allLabels = [...pred.hist_labels, ...pred.future_labels];
  const histData  = [...pred.hist_values, ...Array(pred.future_labels.length).fill(null)];
  const predData  = [...Array(pred.hist_labels.length).fill(null), ...pred.future_values];

  // Connect last historical point to first predicted
  if (pred.hist_values.length > 0) {
    predData[pred.hist_labels.length - 1] = pred.hist_values[pred.hist_values.length - 1];
  }

  charts.prediction = new Chart(ctx, {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: [
        {
          label: 'Historical',
          data: histData,
          borderColor: '#4a90e2',
          backgroundColor: gradHist,
          borderWidth: 2,
          pointRadius: 2,
          fill: true,
          tension: 0.4,
          spanGaps: false,
        },
        {
          label: 'AI Predicted',
          data: predData,
          borderColor: '#00e5c0',
          backgroundColor: gradPred,
          borderWidth: 2,
          borderDash: [6, 3],
          pointRadius: 3,
          pointBackgroundColor: '#00e5c0',
          fill: true,
          tension: 0.4,
          spanGaps: false,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          labels: { usePointStyle: true, pointStyleWidth: 8, padding: 16 }
        },
        tooltip: {
          backgroundColor: 'rgba(13,27,42,0.95)',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { maxTicksLimit: 12 }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { callback: v => v.toLocaleString() }
        }
      }
    }
  });

  // Update badge and summary
  const badge = document.getElementById('predBadge');
  const dir   = pred.direction === 'increase' ? '↑' : '↓';
  badge.textContent = `${dir} ${pred.trend_pct}% projected`;
  badge.style.color = pred.direction === 'increase' ? '#ef4444' : '#10b981';

  document.getElementById('predSummary').textContent = pred.summary;
}


// ── Kick off ──────────────────────────────────────────────────────────────
loadDashboard();
loadAIDashboard();
