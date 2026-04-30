"""Generates crowding_dashboard.html with crowding.json embedded inline."""
import json
from pathlib import Path

here = Path(__file__).parent
data = json.loads((here / "crowding.json").read_text())
data_js = json.dumps(data, separators=(",", ":"))

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Crowding Agent &mdash; 13F Crowding Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0b0d12;
    --panel: #131722;
    --panel2: #1a1f2e;
    --border: #232a3a;
    --text: #e6e9ef;
    --muted: #8a93a6;
    --accent: #ffb547;
    --hot: #ff5d5d;
    --warm: #ff9f43;
    --cool: #5db8ff;
    --green: #38d39f;
    --mono: 'SF Mono', 'Menlo', 'Consolas', ui-monospace, monospace;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
  .wrap {{ max-width: 1400px; margin: 0 auto; padding: 28px 32px 64px; }}
  header {{ display: flex; justify-content: space-between; align-items: flex-start;
    border-bottom: 1px solid var(--border); padding-bottom: 18px; margin-bottom: 22px; }}
  header h1 {{ margin: 0 0 6px 0; font-size: 22px; letter-spacing: 0.2px; font-weight: 600; }}
  header .sub {{ color: var(--muted); font-size: 13px; }}
  .pill {{ display: inline-block; padding: 4px 10px; border-radius: 999px;
    background: rgba(255,181,71,0.12); color: var(--accent); font-size: 11px;
    text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
  .pill.warn {{ background: rgba(255,93,93,0.12); color: var(--hot); }}
  .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 22px; }}
  .kpi {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; }}
  .kpi .label {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; }}
  .kpi .value {{ font-size: 24px; font-weight: 600; margin-top: 4px; font-variant-numeric: tabular-nums; }}
  .kpi .sub2 {{ color: var(--muted); font-size: 12px; margin-top: 4px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 22px; }}
  .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px; }}
  .panel h2 {{ margin: 0 0 14px 0; font-size: 14px; font-weight: 600; letter-spacing: 0.2px; }}
  .panel h2 .hint {{ color: var(--muted); font-size: 12px; font-weight: 400; margin-left: 8px; }}
  .toolbar {{ display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }}
  .toolbar input {{ background: var(--panel2); border: 1px solid var(--border); color: var(--text);
    padding: 8px 12px; border-radius: 6px; font-size: 13px; min-width: 240px; outline: none; }}
  .toolbar input:focus {{ border-color: var(--accent); }}
  .toolbar .count {{ color: var(--muted); font-size: 12px; font-variant-numeric: tabular-nums; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 10px 12px; color: var(--muted); font-weight: 500;
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border); cursor: pointer; user-select: none; white-space: nowrap; }}
  th:hover {{ color: var(--text); }}
  th.right, td.right {{ text-align: right; font-variant-numeric: tabular-nums; }}
  th .arrow {{ color: var(--accent); margin-left: 4px; }}
  tbody tr {{ border-bottom: 1px solid var(--border); cursor: pointer; }}
  tbody tr:hover {{ background: rgba(255,181,71,0.04); }}
  tbody tr.expanded {{ background: var(--panel2); }}
  td {{ padding: 11px 12px; vertical-align: middle; }}
  td.name {{ font-weight: 500; }}
  td.cusip {{ font-family: var(--mono); color: var(--muted); font-size: 12px; }}
  .score {{ display: inline-flex; align-items: center; gap: 8px; min-width: 90px; }}
  .score-bar {{ width: 60px; height: 6px; background: var(--panel2); border-radius: 3px; overflow: hidden; }}
  .score-bar > div {{ height: 100%; border-radius: 3px; }}
  .score-num {{ font-variant-numeric: tabular-nums; font-weight: 600; }}
  .heat-hot {{ background: var(--hot); }}
  .heat-warm {{ background: var(--warm); }}
  .heat-cool {{ background: var(--cool); }}
  .detail {{ background: var(--panel2); padding: 16px 20px; }}
  .detail h3 {{ margin: 0 0 10px 0; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }}
  .detail-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px 18px; }}
  .detail-row {{ display: flex; justify-content: space-between; font-size: 13px;
    padding: 4px 0; border-bottom: 1px dashed var(--border); }}
  .detail-row .v {{ font-variant-numeric: tabular-nums; color: var(--muted); }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px;
    font-size: 11px; font-weight: 600; }}
  .badge.hot {{ background: rgba(255,93,93,0.15); color: var(--hot); }}
  .badge.warm {{ background: rgba(255,159,67,0.15); color: var(--warm); }}
  .badge.cool {{ background: rgba(93,184,255,0.15); color: var(--cool); }}
  footer {{ margin-top: 24px; color: var(--muted); font-size: 11px; line-height: 1.6; }}
  .funds-list {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }}
  .funds-list .fund-chip {{ background: var(--panel2); border: 1px solid var(--border);
    border-radius: 4px; padding: 3px 8px; font-size: 11px; color: var(--muted); }}
  canvas {{ max-height: 320px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>Crowding Agent <span class="pill">13F Monitor</span></h1>
      <div class="sub">Per-stock crowding scores aggregated across <span id="fundCount"></span> institutional funds.
        Quarter end: <span id="reportDate"></span>.</div>
    </div>
    <div style="text-align: right;">
      <span id="dataPill" class="pill warn">Demo data</span>
      <div class="sub" style="margin-top: 6px;">Run <code>fetch_13f.py</code> with EDGAR access for live data.</div>
    </div>
  </header>

  <div class="kpis">
    <div class="kpi">
      <div class="label">Crowded names</div>
      <div class="value" id="kpiNames"></div>
      <div class="sub2">held by 2+ funds</div>
    </div>
    <div class="kpi">
      <div class="label">Most crowded</div>
      <div class="value" id="kpiTop"></div>
      <div class="sub2"><span id="kpiTopScore"></span> / 100 score</div>
    </div>
    <div class="kpi">
      <div class="label">Funds covered</div>
      <div class="value" id="kpiFunds"></div>
      <div class="sub2">institutional 13F filers</div>
    </div>
    <div class="kpi">
      <div class="label">Aggregate $ at risk</div>
      <div class="value" id="kpiAum"></div>
      <div class="sub2">in top-10 crowded names</div>
    </div>
  </div>

  <div class="grid">
    <div class="panel">
      <h2>Top 10 by Crowding Score <span class="hint">red = hot &middot; orange = warm</span></h2>
      <canvas id="chart"></canvas>
    </div>
    <div class="panel">
      <h2>How the score works</h2>
      <p style="font-size: 13px; line-height: 1.6; color: var(--muted); margin: 0 0 12px;">
        Each stock gets a 0&ndash;100 crowding score combining two factors:
      </p>
      <div style="font-size: 13px; line-height: 1.7;">
        <div><span class="badge hot">60%</span> &nbsp;Holders concentration &mdash; share of monitored funds holding the name</div>
        <div style="margin-top: 8px;"><span class="badge warm">40%</span> &nbsp;Capital concentration &mdash; log-scaled total dollar value across the cohort</div>
      </div>
      <p style="font-size: 12px; line-height: 1.6; color: var(--muted); margin: 14px 0 0;">
        Names held by only one fund are excluded. Scores are relative to the cohort, not absolute &mdash;
        a 90+ score means that name is the most consensus position in this universe.
        Use this as a risk lens: high-score names face faster unwinds when sentiment turns.
      </p>
    </div>
  </div>

  <div class="panel">
    <div class="toolbar">
      <input id="filter" placeholder="Filter by issuer or CUSIP…" />
      <span class="count" id="rowCount"></span>
      <span style="flex: 1;"></span>
      <span class="sub" style="font-size: 11px; color: var(--muted);">Click a row to see which funds hold it</span>
    </div>
    <table>
      <thead>
        <tr>
          <th data-sort="rank">#</th>
          <th data-sort="name">Issuer</th>
          <th data-sort="cusip">CUSIP</th>
          <th class="right" data-sort="crowding_score">Crowding</th>
          <th class="right" data-sort="n_holders">Holders</th>
          <th class="right" data-sort="total_value_thousands">Total Value</th>
          <th data-sort="heat">Heat</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>

  <footer>
    <div><strong>Data source:</strong> <span id="dataSource"></span></div>
    <div><strong>Methodology:</strong> <span id="methodology"></span></div>
    <div style="margin-top: 8px;">Built as a one-hour prototype. Per-stock crowding only; quarter-over-quarter
      delta detection (initiations / trims), per-fund exposure rollups, and short-interest overlay are natural extensions.</div>
  </footer>
</div>

<script>
const DATA = {data_js};

// ---------- helpers ----------
const fmtUSD = (thousands) => {{
  const v = thousands * 1000;
  if (v >= 1e9) return '$' + (v / 1e9).toFixed(2) + 'B';
  if (v >= 1e6) return '$' + (v / 1e6).toFixed(1) + 'M';
  return '$' + (v / 1e3).toFixed(0) + 'K';
}};
const heatClass = (s) => s >= 80 ? 'hot' : s >= 60 ? 'warm' : 'cool';
const heatLabel = (s) => s >= 80 ? 'Hot' : s >= 60 ? 'Warm' : 'Cool';
const heatBarClass = (s) => 'heat-' + heatClass(s);

// ---------- header / KPIs ----------
document.getElementById('fundCount').textContent = DATA.fund_count;
const dates = Object.values(DATA.report_dates);
const uniq = [...new Set(dates)];
document.getElementById('reportDate').textContent = uniq.length === 1 ? uniq[0] : uniq.join(', ');
document.getElementById('kpiNames').textContent = DATA.records.length;
document.getElementById('kpiTop').textContent = DATA.records[0].name.replace(/ INC$| CORP$| CO$| CL [AB]$/, '');
document.getElementById('kpiTopScore').textContent = DATA.records[0].crowding_score;
document.getElementById('kpiFunds').textContent = DATA.fund_count;
const aum = DATA.records.slice(0, 10).reduce((s, r) => s + r.total_value_thousands, 0);
document.getElementById('kpiAum').textContent = fmtUSD(aum);
document.getElementById('dataSource').textContent = DATA.data_source || 'SEC EDGAR live';
document.getElementById('methodology').textContent = DATA.methodology;
if (!DATA.data_source || !DATA.data_source.includes('synthetic')) {{
  const pill = document.getElementById('dataPill');
  pill.classList.remove('warn');
  pill.textContent = 'EDGAR live';
}}

// ---------- chart ----------
const top = DATA.records.slice(0, 10);
const colors = top.map(r => r.crowding_score >= 80 ? '#ff5d5d' : r.crowding_score >= 60 ? '#ff9f43' : '#5db8ff');
new Chart(document.getElementById('chart'), {{
  type: 'bar',
  data: {{
    labels: top.map(r => r.name.replace(/ INC$| CORP$| CO$| CL [AB]$/, '')),
    datasets: [{{
      data: top.map(r => r.crowding_score),
      backgroundColor: colors,
      borderRadius: 4,
    }}],
  }},
  options: {{
    indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ color: '#8a93a6' }}, grid: {{ color: 'rgba(255,255,255,0.04)' }}, max: 100 }},
      y: {{ ticks: {{ color: '#e6e9ef', font: {{ size: 12 }} }}, grid: {{ display: false }} }},
    }},
  }},
}});

// ---------- table ----------
let sortKey = 'crowding_score';
let sortDir = -1;
let filterText = '';

const tbody = document.getElementById('tbody');
const rowCount = document.getElementById('rowCount');

function render() {{
  const q = filterText.trim().toLowerCase();
  let rows = DATA.records.filter(r =>
    !q || r.name.toLowerCase().includes(q) || r.cusip.toLowerCase().includes(q)
  );
  rows.sort((a, b) => {{
    let av, bv;
    if (sortKey === 'rank') {{ av = a.crowding_score; bv = b.crowding_score; }}
    else if (sortKey === 'heat') {{ av = a.crowding_score; bv = b.crowding_score; }}
    else {{ av = a[sortKey]; bv = b[sortKey]; }}
    if (typeof av === 'string') return av.localeCompare(bv) * sortDir;
    return (av - bv) * sortDir;
  }});

  tbody.innerHTML = '';
  rows.forEach((r, i) => {{
    const tr = document.createElement('tr');
    tr.dataset.cusip = r.cusip;
    tr.innerHTML = `
      <td>${{i + 1}}</td>
      <td class="name">${{r.name}}</td>
      <td class="cusip">${{r.cusip}}</td>
      <td class="right">
        <span class="score">
          <span class="score-bar"><div class="${{heatBarClass(r.crowding_score)}}" style="width: ${{r.crowding_score}}%;"></div></span>
          <span class="score-num">${{r.crowding_score.toFixed(1)}}</span>
        </span>
      </td>
      <td class="right">${{r.n_holders}} / ${{DATA.fund_count}}</td>
      <td class="right">${{fmtUSD(r.total_value_thousands)}}</td>
      <td><span class="badge ${{heatClass(r.crowding_score)}}">${{heatLabel(r.crowding_score)}}</span></td>
    `;
    tr.addEventListener('click', () => toggleDetail(tr, r));
    tbody.appendChild(tr);
  }});
  rowCount.textContent = `${{rows.length}} of ${{DATA.records.length}} crowded names`;
}}

function toggleDetail(tr, r) {{
  const next = tr.nextElementSibling;
  if (next && next.classList.contains('detail-row-tr')) {{
    next.remove();
    tr.classList.remove('expanded');
    return;
  }}
  // collapse any other open
  document.querySelectorAll('.detail-row-tr').forEach(n => n.remove());
  document.querySelectorAll('tr.expanded').forEach(n => n.classList.remove('expanded'));
  tr.classList.add('expanded');

  const dtr = document.createElement('tr');
  dtr.classList.add('detail-row-tr');
  const td = document.createElement('td');
  td.colSpan = 7;
  td.classList.add('detail');
  const totalK = r.total_value_thousands;
  const lines = r.funds.map(f => {{
    const pct = ((f.value_thousands / totalK) * 100).toFixed(1);
    return `<div class="detail-row"><span>${{f.fund}}</span><span class="v">${{fmtUSD(f.value_thousands)}} &middot; ${{pct}}%</span></div>`;
  }}).join('');
  td.innerHTML = `
    <h3>${{r.n_holders}} funds hold ${{r.name}} &mdash; ${{fmtUSD(totalK)}} aggregate</h3>
    <div class="detail-grid">${{lines}}</div>
  `;
  dtr.appendChild(td);
  tr.parentNode.insertBefore(dtr, tr.nextSibling);
}}

document.getElementById('filter').addEventListener('input', e => {{
  filterText = e.target.value;
  render();
}});

document.querySelectorAll('th[data-sort]').forEach(th => {{
  th.addEventListener('click', () => {{
    const key = th.dataset.sort;
    if (key === sortKey) sortDir *= -1;
    else {{ sortKey = key; sortDir = (key === 'name' || key === 'cusip') ? 1 : -1; }}
    document.querySelectorAll('th .arrow').forEach(a => a.remove());
    const arrow = document.createElement('span');
    arrow.className = 'arrow';
    arrow.textContent = sortDir === 1 ? '↑' : '↓';
    th.appendChild(arrow);
    render();
  }});
}});

render();
// initial sort indicator
const initTh = document.querySelector('th[data-sort="crowding_score"]');
const arrow = document.createElement('span');
arrow.className = 'arrow';
arrow.textContent = '↓';
initTh.appendChild(arrow);
</script>
</body>
</html>
"""

(here / "crowding_dashboard.html").write_text(html)
print(f"wrote {(here / 'crowding_dashboard.html').stat().st_size:,} bytes")
