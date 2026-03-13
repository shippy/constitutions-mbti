"""Generate interactive UMAP visualization with switchable dimension lenses."""

import json
from pathlib import Path

from src.config import DATA_RESULTS, OUTPUTS


def build_html(all_results: dict) -> str:
    """Build a self-contained interactive HTML page."""

    # Pre-process per-lens data for JS
    lenses_js = {}
    for lens_id, result in all_results.items():
        archetypes = result["archetypes"]
        assignments = result["country_assignments"]

        lenses_js[lens_id] = {
            "name": result["dimension_set"]["name"],
            "description": result["dimension_set"]["description"],
            "dimensions": result["dimension_set"]["dimensions"],
            "archetypes": {
                str(cid): {
                    "name": a["name"],
                    "description": a.get("description", ""),
                    "key_themes": a.get("key_themes", []),
                    "mbti": a.get("mbti", "????"),
                    "avg_scores": a.get("avg_scores", {}),
                }
                for cid, a in archetypes.items()
            },
            "countries": [
                {
                    "country_id": a["country_id"],
                    "country": a["country_id"].replace("_", " "),
                    "cluster": a["cluster"],
                    "mbti": a.get("mbti", "????"),
                    "scores": a.get("scores", {}),
                    "x": a["umap_x"],
                    "y": a["umap_y"],
                }
                for a in assignments
            ],
        }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Constitutional Personality Map</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;700;800&family=JetBrains+Mono:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #121212;
    color: #ffffff;
    overflow-x: hidden;
  }}
  .header {{
    padding: 20px 32px 16px;
    background: #121212;
    border-bottom: 1px solid #2a2a2a;
  }}
  .header h1 {{
    font-size: 26px;
    font-weight: 800;
    color: #fe6019;
    margin-bottom: 2px;
  }}
  .header p {{ color: rgba(255,255,255,0.6); font-size: 13px; font-weight: 300; }}
  .controls {{
    display: flex;
    gap: 10px;
    padding: 12px 32px;
    background: #121212;
    border-bottom: 1px solid #2a2a2a;
    flex-wrap: wrap;
    align-items: center;
  }}
  .controls label {{
    font-size: 12px;
    color: rgba(255,255,255,0.6);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .lens-btn {{
    padding: 7px 14px;
    border: 1px solid #333;
    border-radius: 20px;
    background: transparent;
    color: rgba(255,255,255,0.6);
    cursor: pointer;
    font-family: 'Poppins', sans-serif;
    font-size: 12px;
    font-weight: 400;
    transition: all 0.2s;
  }}
  .lens-btn:hover {{ border-color: #fe6019; color: #fff; }}
  .lens-btn.active {{
    background: #fe6019;
    border-color: #fe6019;
    color: #fff;
    font-weight: 700;
  }}
  .main {{
    display: grid;
    grid-template-columns: 1fr 380px;
    height: calc(100vh - 120px);
  }}
  .chart-container {{
    position: relative;
    overflow: hidden;
    background: #121212;
  }}
  canvas {{ display: block; width: 100%; height: 100%; }}
  .sidebar {{
    background: #1e1e1e;
    border-left: 1px solid #2a2a2a;
    overflow-y: auto;
    padding: 16px 20px;
  }}
  .dimension-guide {{
    background: #121212;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 20px;
  }}
  .dimension-guide h2 {{
    font-size: 14px;
    color: #fe6019;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
  }}
  .dimension-guide .lens-desc {{
    font-size: 12px;
    color: rgba(255,255,255,0.6);
    margin-bottom: 12px;
    font-style: italic;
    font-weight: 300;
  }}
  .dim-block {{
    padding: 10px 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }}
  .dim-block:last-child {{ border-bottom: none; }}
  .dim-block .dim-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }}
  .dim-block .dim-header .letters {{
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px;
    white-space: nowrap;
  }}
  .dim-block .dim-header .letters .pos {{ color: #fe6019; }}
  .dim-block .dim-header .letters .neg {{ color: rgba(255,255,255,0.5); }}
  .dim-block .dim-header .letters .slash {{ color: #444; }}
  .dim-pole {{
    display: flex;
    gap: 8px;
    margin: 4px 0 4px 28px;
    font-size: 11px;
    line-height: 1.4;
  }}
  .dim-pole .pole-letter {{
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    min-width: 14px;
    flex-shrink: 0;
  }}
  .dim-pole .pole-letter.pos {{ color: #fe6019; }}
  .dim-pole .pole-letter.neg {{ color: rgba(255,255,255,0.5); }}
  .dim-pole .pole-name {{ color: #fff; font-weight: 700; }}
  .dim-pole .pole-desc {{ color: rgba(255,255,255,0.5); font-weight: 300; }}
  .search-box {{
    width: 100%;
    padding: 8px 12px;
    background: #121212;
    border: 1px solid #333;
    border-radius: 8px;
    color: #fff;
    font-family: 'Poppins', sans-serif;
    font-size: 13px;
    margin-bottom: 14px;
    outline: none;
  }}
  .search-box:focus {{ border-color: #fe6019; }}
  .search-box::placeholder {{ color: rgba(255,255,255,0.3); }}
  .section-title {{
    font-size: 12px;
    color: #fe6019;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
  }}
  .archetype-card {{
    background: #121212;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
    border-left-width: 3px;
  }}
  .archetype-card:hover {{ border-color: #fe6019; }}
  .archetype-card .top-row {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 4px;
  }}
  .archetype-card .name {{ font-weight: 700; font-size: 14px; }}
  .archetype-card .mbti {{
    font-size: 16px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
  }}
  .archetype-card .desc {{
    font-size: 11px;
    color: rgba(255,255,255,0.5);
    line-height: 1.5;
    font-weight: 300;
    margin-bottom: 4px;
  }}
  .archetype-card .count {{ font-size: 11px; color: rgba(255,255,255,0.3); }}
  .tooltip {{
    position: absolute;
    background: #1e1e1e;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s;
    z-index: 100;
    max-width: 300px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.6);
  }}
  .tooltip .tt-country {{ font-weight: 700; font-size: 15px; color: #fff; }}
  .tooltip .tt-archetype {{ color: #fe6019; font-size: 12px; margin: 3px 0; }}
  .tooltip .tt-mbti {{ font-size: 22px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }}
  .tooltip .tt-scores {{ font-size: 11px; color: rgba(255,255,255,0.5); margin-top: 6px; font-weight: 300; }}
  .tooltip .tt-scores span {{ display: inline-block; margin-right: 8px; }}
  .footer {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 8px 32px;
    background: #121212;
    border-top: 1px solid #2a2a2a;
    font-size: 11px;
    color: rgba(255,255,255,0.3);
    font-weight: 300;
    z-index: 50;
  }}
  .footer a {{ color: rgba(255,255,255,0.5); text-decoration: none; }}
  .footer a:hover {{ color: #fe6019; }}
</style>
</head>
<body>
<div class="header">
  <h1>Constitutional Personality Map</h1>
  <p>193 national constitutions scored on personality dimensions, clustered, and typed</p>
</div>
<div class="controls">
  <label>Lens:</label>
  <div id="lens-buttons"></div>
</div>
<div class="main">
  <div class="chart-container">
    <canvas id="chart"></canvas>
    <div class="tooltip" id="tooltip"></div>
  </div>
  <div class="sidebar">
    <div class="dimension-guide" id="dimension-guide"></div>
    <input type="text" class="search-box" id="search" placeholder="Search countries...">
    <div class="section-title">Archetypes</div>
    <div id="archetype-list"></div>
  </div>
</div>
<div class="footer">
  Built by <a href="https://simonpodhajsky.com">Simon Podhajsk&yacute;</a> &amp; Claude &middot;
  Inspired by <a href="https://www.linkedin.com/in/gwynethwindflower/">Gwyneth Windflower</a> asking "what if constitutions had MBTI types?" &middot;
  Data from <a href="https://constituteproject.org">Constitute Project</a>
</div>

<script>
const lenses = {json.dumps(lenses_js)};

// Colors organized by MBTI dimensions:
// E = warm (oranges/reds/ambers), I = cool (blues/teals/slate)
// N = more vivid, S = more muted/earthy
// J = deeper, P = lighter
const MBTI_COLORS = {{
  // I_S_ — cool, muted
  'ISTJ': '#5b7fa6',  // dusty steel blue
  'ISFJ': '#6a9b8a',  // sage green
  'ISTP': '#7daab5',  // light teal
  'ISFP': '#8abfa5',  // soft mint
  // I_N_ — cool, vivid
  'INTJ': '#5e5eb5',  // indigo
  'INFJ': '#8b6aaf',  // soft purple
  'INTP': '#6ba3d6',  // bright blue
  'INFP': '#b088c8',  // lavender
  // E_S_ — warm, muted
  'ESTJ': '#c27a3a',  // amber
  'ESFJ': '#b5694d',  // terracotta
  'ESTP': '#d4944a',  // warm gold
  'ESFP': '#d6a656',  // honey
  // E_N_ — warm, vivid
  'ENTJ': '#d45a2a',  // burnt orange (near your #fe6019)
  'ENFJ': '#e07040',  // coral
  'ENTP': '#e8985a',  // apricot
  'ENFP': '#e86060',  // warm red
}};

let currentLens = Object.keys(lenses)[0];
let hoveredIdx = -1;
let searchQuery = '';

const canvas = document.getElementById('chart');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');
let dpr = window.devicePixelRatio || 1;
let viewX = 0, viewY = 0, viewScale = 1;
let isDragging = false, dragStartX = 0, dragStartY = 0;

function getLens() {{ return lenses[currentLens]; }}
function getCountries() {{ return getLens().countries; }}

function resizeCanvas() {{
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  canvas.style.width = rect.width + 'px';
  canvas.style.height = rect.height + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}}

function resetView() {{
  const countries = getCountries();
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const c of countries) {{
    minX = Math.min(minX, c.x); maxX = Math.max(maxX, c.x);
    minY = Math.min(minY, c.y); maxY = Math.max(maxY, c.y);
  }}
  const rect = canvas.parentElement.getBoundingClientRect();
  const padX = (maxX - minX) * 0.12;
  const padY = (maxY - minY) * 0.12;
  const scaleX = rect.width / (maxX - minX + 2 * padX);
  const scaleY = rect.height / (maxY - minY + 2 * padY);
  viewScale = Math.min(scaleX, scaleY);
  viewX = rect.width / 2 - ((minX + maxX) / 2) * viewScale;
  viewY = rect.height / 2 - ((minY + maxY) / 2) * viewScale;
}}

function toScreen(x, y) {{
  return {{ x: x * viewScale + viewX, y: y * viewScale + viewY }};
}}

function draw() {{
  const rect = canvas.parentElement.getBoundingClientRect();
  ctx.clearRect(0, 0, rect.width, rect.height);

  const countries = getCountries();
  const lens = getLens();
  const matchSet = searchQuery
    ? new Set(countries.filter(c => c.country.toLowerCase().includes(searchQuery)).map(c => c.country_id))
    : null;

  for (let i = 0; i < countries.length; i++) {{
    const c = countries[i];
    const s = toScreen(c.x, c.y);
    const color = MBTI_COLORS[c.mbti] || '#666';
    const isMatch = !matchSet || matchSet.has(c.country_id);
    const isHovered = i === hoveredIdx;

    ctx.globalAlpha = isMatch ? 1.0 : 0.12;
    ctx.beginPath();
    ctx.arc(s.x, s.y, isHovered ? 9 : 5, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    if (isHovered) {{
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
    }}

    if (viewScale > 25 || isHovered || (isMatch && matchSet)) {{
      ctx.fillStyle = isMatch ? 'rgba(255,255,255,0.8)' : 'rgba(255,255,255,0.15)';
      ctx.font = `${{isHovered ? '700 13px' : '400 10px'}} Poppins, sans-serif`;
      ctx.textAlign = 'center';
      ctx.fillText(c.country, s.x, s.y - 10);
    }}
  }}
  ctx.globalAlpha = 1.0;
  requestAnimationFrame(draw);
}}

function findNearest(mx, my) {{
  const countries = getCountries();
  let best = -1, bestDist = 20;
  for (let i = 0; i < countries.length; i++) {{
    const s = toScreen(countries[i].x, countries[i].y);
    const d = Math.hypot(s.x - mx, s.y - my);
    if (d < bestDist) {{ bestDist = d; best = i; }}
  }}
  return best;
}}

function fmtScore(v) {{
  return v >= 0 ? '+' + v.toFixed(2) : v.toFixed(2);
}}

canvas.addEventListener('mousemove', e => {{
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;

  if (isDragging) {{
    viewX += e.clientX - dragStartX;
    viewY += e.clientY - dragStartY;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    return;
  }}

  hoveredIdx = findNearest(mx, my);
  if (hoveredIdx >= 0) {{
    const c = getCountries()[hoveredIdx];
    const lens = getLens();
    const arch = lens.archetypes[String(c.cluster)];
    const dims = lens.dimensions;
    const sc = c.scores || {{}};
    tooltip.innerHTML = `
      <div class="tt-country">${{c.country}}</div>
      <div class="tt-archetype">${{arch?.name || '?'}}</div>
      <div class="tt-mbti" style="color:${{MBTI_COLORS[c.mbti] || '#fff'}}">${{c.mbti}}</div>
      <div class="tt-scores">
        <span>${{dims.E_I?.name}}: ${{fmtScore(sc.E_I || 0)}}</span>
        <span>${{dims.S_N?.name}}: ${{fmtScore(sc.S_N || 0)}}</span>
        <span>${{dims.T_F?.name}}: ${{fmtScore(sc.T_F || 0)}}</span>
        <span>${{dims.J_P?.name}}: ${{fmtScore(sc.J_P || 0)}}</span>
      </div>
    `;
    tooltip.style.opacity = '1';
    // Keep tooltip in bounds
    const tx = Math.min(mx + 16, rect.width - 310);
    const ty = Math.min(my - 10, rect.height - 120);
    tooltip.style.left = tx + 'px';
    tooltip.style.top = ty + 'px';
    canvas.style.cursor = 'pointer';
  }} else {{
    tooltip.style.opacity = '0';
    canvas.style.cursor = isDragging ? 'grabbing' : 'grab';
  }}
}});

canvas.addEventListener('mousedown', e => {{
  isDragging = true;
  dragStartX = e.clientX;
  dragStartY = e.clientY;
  canvas.style.cursor = 'grabbing';
}});
canvas.addEventListener('mouseup', () => {{ isDragging = false; canvas.style.cursor = 'grab'; }});
canvas.addEventListener('mouseleave', () => {{
  isDragging = false; hoveredIdx = -1; tooltip.style.opacity = '0';
}});
canvas.addEventListener('wheel', e => {{
  e.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const factor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
  viewX = mx - (mx - viewX) * factor;
  viewY = my - (my - viewY) * factor;
  viewScale *= factor;
}}, {{ passive: false }});

function switchLens(lensId) {{
  currentLens = lensId;
  hoveredIdx = -1;
  resetView();
  renderLensButtons();
  renderSidebar();
}}

function renderLensButtons() {{
  const container = document.getElementById('lens-buttons');
  container.innerHTML = '';
  for (const [id, lens] of Object.entries(lenses)) {{
    const btn = document.createElement('button');
    btn.className = 'lens-btn' + (id === currentLens ? ' active' : '');
    btn.textContent = lens.name;
    btn.onclick = () => switchLens(id);
    container.appendChild(btn);
  }}
}}

function renderSidebar() {{
  const lens = getLens();

  // Dimension guide (prominent, at top, full write-up)
  const guide = document.getElementById('dimension-guide');
  guide.innerHTML = `<h2>${{lens.name}}</h2><div class="lens-desc">${{lens.description}}</div>`;
  for (const [key, dim] of Object.entries(lens.dimensions)) {{
    const [first, second] = key.split('_');
    guide.innerHTML += `
      <div class="dim-block">
        <div class="dim-header">
          <span class="letters"><span class="pos">${{first}}</span><span class="slash">/</span><span class="neg">${{second}}</span></span>
        </div>
        <div class="dim-pole">
          <span class="pole-letter pos">${{first}}</span>
          <span><span class="pole-name">${{dim[first + '_label']}}</span> &mdash; <span class="pole-desc">${{dim[first + '_desc']}}</span></span>
        </div>
        <div class="dim-pole">
          <span class="pole-letter neg">${{second}}</span>
          <span><span class="pole-name">${{dim[second + '_label']}}</span> &mdash; <span class="pole-desc">${{dim[second + '_desc']}}</span></span>
        </div>
      </div>
    `;
  }}

  // Archetype cards
  const list = document.getElementById('archetype-list');
  list.innerHTML = '';
  const countries = getCountries();
  const clusterIds = Object.keys(lens.archetypes).sort((a, b) => Number(a) - Number(b));

  for (const cid of clusterIds) {{
    const arch = lens.archetypes[cid];
    const count = countries.filter(c => c.cluster === Number(cid)).length;
    const color = MBTI_COLORS[arch.mbti] || '#666';

    const card = document.createElement('div');
    card.className = 'archetype-card';
    card.style.borderLeftColor = color;
    card.innerHTML = `
      <div class="top-row">
        <span class="name" style="color: ${{color}}">${{arch.name}}</span>
        <span class="mbti" style="color: ${{color}}">${{arch.mbti}}</span>
      </div>
      <div class="desc">${{arch.description}}</div>
      <div class="count">${{count}} countries</div>
    `;
    list.appendChild(card);
  }}
}}

document.getElementById('search').addEventListener('input', e => {{
  searchQuery = e.target.value.toLowerCase();
}});

window.addEventListener('resize', () => {{ resizeCanvas(); resetView(); }});
resizeCanvas();
resetView();
renderLensButtons();
renderSidebar();
draw();
</script>
</body>
</html>"""


def main() -> None:
    out_dir = Path(OUTPUTS)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_results = json.loads((Path(DATA_RESULTS) / "archetypes.json").read_text())

    html = build_html(all_results)
    html_path = out_dir / "constitution_map.html"
    html_path.write_text(html)
    print(f"Saved interactive map to {html_path}")

    # Typology JSON
    typology = {"lenses": {}}
    for lens_id, result in all_results.items():
        typology["lenses"][lens_id] = {
            "name": result["dimension_set"]["name"],
            "archetypes": [
                {
                    "id": int(cid),
                    "name": a["name"],
                    "description": a.get("description", ""),
                    "key_themes": a.get("key_themes", []),
                    "mbti": a.get("mbti", "????"),
                    "avg_scores": a.get("avg_scores", {}),
                    "countries": a.get("countries", []),
                }
                for cid, a in sorted(result["archetypes"].items(), key=lambda x: int(x[0]))
            ],
            "countries": [
                {
                    "country": a["country_id"].replace("_", " "),
                    "country_id": a["country_id"],
                    "cluster": a["cluster"],
                    "mbti": a.get("mbti", "????"),
                    "scores": a.get("scores", {}),
                    "umap_x": a["umap_x"],
                    "umap_y": a["umap_y"],
                }
                for a in result["country_assignments"]
            ],
        }

    typology_path = out_dir / "typology.json"
    typology_path.write_text(json.dumps(typology, indent=2, ensure_ascii=False))
    print(f"Saved typology to {typology_path}")
    print(f"{len(typology['lenses'])} lenses")


if __name__ == "__main__":
    main()
