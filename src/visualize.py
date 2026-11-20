"""Generate interactive UMAP visualization with switchable dimension lenses."""

import json
import re
from pathlib import Path

from src.config import DATA_RESULTS, OUTPUTS

# Short, recognisable names for Constitute Project ids that read badly when de-underscored.
DISPLAY_NAMES = {
    "Congo_the": "Republic of the Congo",
    "Democratic_Republic_of_the_Congo": "DR Congo",
    "Democratic_People_s_Republic_of_Korea_the": "North Korea",
    "Republic_of_Korea__the": "South Korea",
    "Lao_People_s_Democratic_Republic__the": "Laos",
    "Russian_Federation__the": "Russia",
    "Syrian_Arab_Republic_the": "Syria",
    "United_Kingdom_of_Great_Britain_and_Northern_Ireland__the": "United Kingdom",
    "United_Republic_of_Tanzania__the": "Tanzania",
    "United_States_of_America": "United States",
    "Iran_Islamic_Rep_of_": "Iran",
    "Micronesia__Fed_States_of_": "Micronesia",
    "Republic_of_Moldova": "Moldova",
    "Brunei_Darussalam": "Brunei",
    "Viet_Nam": "Vietnam",
    "Cote_d_Ivoire": "Côte d’Ivoire",
    "Sao_Tome_and_Principe": "São Tomé and Príncipe",
    "The_former_Yugoslav_Republic_of_Macedonia": "North Macedonia",
    "Swaziland": "Eswatini",
}


def display_name(country_id: str) -> str:
    """Human-readable country name from a Constitute Project id."""
    if country_id in DISPLAY_NAMES:
        return DISPLAY_NAMES[country_id]
    name = re.sub(r"_+the$", "", country_id)
    return re.sub(r"_+", " ", name).strip()


def lens_payload(all_results: dict) -> dict:
    """Reduce pipeline results to the per-lens data the page needs."""
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
                    "country": display_name(a["country_id"]),
                    "cluster": a["cluster"],
                    "mbti": a.get("mbti", "????"),
                    "scores": a.get("scores", {}),
                    "x": a["umap_x"],
                    "y": a["umap_y"],
                }
                for a in assignments
            ],
        }
    return lenses_js


def render_html(lenses_js: dict) -> str:
    """Render the self-contained page around pre-processed lens data."""
    # Escape every "<" so no "</script>" or "<!--" sequence can occur inside the <script> block.
    data = json.dumps(lenses_js, ensure_ascii=False).replace("<", "\\u003c")
    return PAGE_TEMPLATE.replace("__LENSES_JSON__", data)


def build_html(all_results: dict) -> str:
    """Build a self-contained interactive HTML page."""
    return render_html(lens_payload(all_results))


PAGE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>The Constitutional Personality Map</title>
<meta name="description" content="193 national constitutions, scored on four personality axes, clustered into archetypes and assigned a Myers–Briggs type.">
<meta name="theme-color" content="#f8f5ee">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Libre+Caslon+Text:ital,wght@0,400;0,700;1,400&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --paper: oklch(97.6% 0.009 85);
    --paper-2: oklch(95.2% 0.013 85);
    --ink: oklch(23% 0.015 60);
    --ink-2: oklch(41% 0.014 60);
    --ink-3: oklch(50% 0.012 60);
    --rule: oklch(85% 0.012 75);
    --seal: oklch(49% 0.17 28);
    --seal-wash: oklch(93.5% 0.03 45);
    --font-display: "Libre Caslon Text", "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
    --font-ui: "Public Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    --gutter: clamp(1rem, 0.6rem + 1.6vw, 2rem);
    --ease-out: cubic-bezier(0.25, 1, 0.5, 1);
    --tap: 44px;
    color-scheme: light;
  }
  *, *::before, *::after { box-sizing: border-box; }
  * { margin: 0; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    background: var(--paper);
    color: var(--ink);
    font-family: var(--font-ui);
    font-size: 1rem;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }
  button, input { font: inherit; color: inherit; }
  button { cursor: pointer; background: none; border: 0; padding: 0; text-align: inherit; }
  :focus-visible { outline: 2px solid var(--seal); outline-offset: 2px; }
  .sr-only {
    position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
    overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
  }

  /* ---------- Masthead ---------- */
  .masthead {
    padding: clamp(1.25rem, 0.8rem + 2vw, 2.75rem) var(--gutter) clamp(1rem, 0.8rem + 1vw, 1.5rem);
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 0.75rem 3rem;
    align-items: end;
  }
  .kicker {
    font-size: 0.8125rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--seal);
  }
  h1 {
    font-family: var(--font-display);
    font-weight: 400;
    font-size: clamp(2.1rem, 1.3rem + 3.6vw, 4.25rem);
    line-height: 1.02;
    letter-spacing: -0.015em;
    text-wrap: balance;
  }
  h1 em { font-style: italic; color: var(--seal); }
  .dek {
    max-width: 38rem;
    color: var(--ink-2);
    font-size: clamp(0.9375rem, 0.9rem + 0.2vw, 1.0625rem);
    text-wrap: pretty;
  }
  @media (min-width: 60rem) {
    .masthead { grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); }
    .masthead .kicker { grid-column: 1 / -1; }
    .dek { padding-bottom: 0.4rem; }
  }

  /* ---------- Lens "articles" ---------- */
  .lenses {
    border-top: 3px double var(--ink);
    border-bottom: 1px solid var(--rule);
    position: relative;
  }
  .lens-row {
    display: flex;
    gap: 0.25rem;
    padding: 0 var(--gutter);
    overflow-x: auto;
    scroll-snap-type: x proximity;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
  }
  .lens-row::-webkit-scrollbar { display: none; }
  @media (max-width: 59.99rem) {
    .lens-row {
      -webkit-mask-image: linear-gradient(to right, #000 85%, transparent);
      mask-image: linear-gradient(to right, #000 85%, transparent);
      padding-right: 3rem;
    }
  }
  .lens-btn {
    flex: none;
    scroll-snap-align: start;
    min-height: var(--tap);
    padding: 0.6rem 0.85rem 0.55rem;
    display: flex;
    align-items: baseline;
    gap: 0.45rem;
    border-bottom: 3px solid transparent;
    margin-bottom: -1px;
    color: var(--ink-2);
    font-weight: 500;
    font-size: 0.9375rem;
    white-space: nowrap;
    transition: color 0.2s var(--ease-out), border-color 0.2s var(--ease-out);
  }
  .lens-btn:first-child { margin-left: -0.85rem; }
  .lens-btn .art {
    font-family: var(--font-display);
    font-style: italic;
    font-size: 0.875rem;
    color: var(--ink-3);
  }
  .lens-btn:hover { color: var(--ink); }
  .lens-btn[aria-pressed="true"] { color: var(--ink); border-bottom-color: var(--seal); font-weight: 600; }
  .lens-btn[aria-pressed="true"] .art { color: var(--seal); }
  .lens-dek {
    padding: 0.8rem var(--gutter) 0;
    font-family: var(--font-display);
    font-style: italic;
    font-size: clamp(1.05rem, 1rem + 0.3vw, 1.25rem);
    color: var(--ink-2);
  }

  /* ---------- Layout ---------- */
  .layout { display: grid; grid-template-columns: minmax(0, 1fr); }
  @media (min-width: 60rem) {
    .layout { grid-template-columns: minmax(0, 1fr) clamp(22rem, 28vw, 27rem); align-items: start; }
    .stage { position: sticky; top: 0; height: 100svh; display: flex; flex-direction: column; }
    .stage .map { flex: 1; min-height: 0; }
    .notes { border-left: 1px solid var(--rule); min-height: 100svh; }
  }

  /* ---------- Stage: search + map + key ---------- */
  .stage { padding: 0.75rem var(--gutter) 1rem; }
  .finder {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem 1rem;
    margin-bottom: 0.75rem;
  }
  .search {
    position: relative;
    flex: 1 1 16rem;
    max-width: 24rem;
  }
  .search label {
    position: absolute; left: 0.85rem; top: 50%; translate: 0 -50%;
    font-size: 0.8125rem; font-weight: 600; color: var(--ink-2); pointer-events: none;
  }
  .search input {
    width: 100%;
    min-height: var(--tap);
    padding: 0.5rem 0.85rem 0.5rem 7.4rem;
    background: var(--paper);
    border: 1px solid var(--ink-3);
    border-radius: 2px;
    font-size: 1rem;
  }
  .search input::placeholder { color: var(--ink-3); }
  .search input:focus { outline: 2px solid var(--seal); outline-offset: -1px; border-color: var(--seal); }
  .status {
    flex: 1 1 14rem;
    font-size: 0.875rem;
    color: var(--ink-2);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-height: var(--tap);
  }
  .status strong { color: var(--ink); font-weight: 600; }
  .link-btn {
    color: var(--seal);
    font-weight: 600;
    text-decoration: underline;
    text-underline-offset: 0.18em;
    min-height: var(--tap);
    padding: 0 0.25rem;
  }

  .map {
    position: relative;
    height: clamp(24rem, 68svh, 42rem);
    background: var(--paper-2);
    border: 1px solid var(--rule);
    overflow: hidden;
  }
  @media (min-width: 60rem) { .map { height: auto; } }
  canvas { display: block; width: 100%; height: 100%; touch-action: pan-y; cursor: grab; }
  canvas.dragging { cursor: grabbing; }
  canvas.on-point { cursor: pointer; }
  .zoom {
    position: absolute; top: 0.5rem; right: 0.5rem;
    display: flex; flex-direction: column;
    background: var(--paper);
    border: 1px solid var(--rule);
  }
  .zoom button {
    width: var(--tap); height: var(--tap);
    display: grid; place-items: center;
    font-size: 1.25rem; line-height: 1; color: var(--ink);
  }
  .zoom button + button { border-top: 1px solid var(--rule); }
  .zoom button:hover { background: var(--paper-2); }
  .zoom svg { width: 18px; height: 18px; stroke: currentColor; fill: none; stroke-width: 1.6; }
  .hint {
    position: absolute; left: 0.75rem; top: 0.6rem;
    font-size: 0.8125rem; color: var(--ink-2);
    pointer-events: none;
    background: color-mix(in oklch, var(--paper-2) 85%, transparent);
    padding: 0.1rem 0.3rem;
    transition: opacity 0.4s var(--ease-out);
  }
  .hint.gone { opacity: 0; }

  /* Selected country */
  .detail {
    position: absolute;
    left: 0.5rem; right: 0.5rem; bottom: 0.5rem;
    max-height: calc(100% - 1rem);
    overflow-y: auto;
    overscroll-behavior: contain;
    background: var(--paper);
    border: 1px solid var(--ink);
    padding: 0.9rem 1rem 1rem;
    transition: opacity 0.25s var(--ease-out), translate 0.3s var(--ease-out);
  }
  @media (min-width: 40rem) { .detail { right: auto; bottom: auto; top: 0.5rem; width: 23rem; } }
  .detail[hidden] { display: block; opacity: 0; translate: 0 0.75rem; pointer-events: none; visibility: hidden; }
  .detail-close {
    position: absolute; top: 0.15rem; right: 0.15rem;
    width: var(--tap); height: var(--tap);
    display: grid; place-items: center;
    color: var(--ink-2); font-size: 1.4rem; line-height: 1;
  }
  .detail-close:hover { color: var(--ink); }
  .detail-arch {
    font-size: 0.8125rem; font-weight: 600; color: var(--seal);
    padding-right: 2.5rem;
  }
  .detail-arch button { text-decoration: underline; text-underline-offset: 0.18em; text-decoration-color: var(--rule); }
  .detail-arch button:hover { text-decoration-color: currentColor; }
  .detail-head { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; margin: 0.1rem 2.25rem 0.7rem 0; }
  .detail-name {
    font-family: var(--font-display); font-weight: 400;
    font-size: 1.6rem; line-height: 1.1;
  }
  .type-tag {
    font-family: var(--font-display);
    font-size: 1.35rem;
    letter-spacing: 0.06em;
    display: inline-flex; align-items: center; gap: 0.4rem;
    white-space: nowrap;
  }
  .sw { display: inline-block; width: 0.7em; height: 0.7em; border-radius: 50%; background: var(--c); flex: none; }
  .axes { list-style: none; padding: 0; display: grid; gap: 0.45rem; }
  .axis {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    grid-template-areas: "a b" "bar bar";
    align-items: end;
    column-gap: 1rem;
    font-size: 0.8125rem;
    color: var(--ink-3);
    line-height: 1.25;
  }
  .axis .pole { grid-area: a; }
  .axis .pole.right { grid-area: b; }
  .axis .bar { grid-area: bar; }
  .axis .pole b { font-family: var(--font-display); font-weight: 700; font-size: 0.9375rem; margin: 0 0.15rem; }
  .axis .pole.right { text-align: right; }
  .axis .pole.on { color: var(--ink); font-weight: 600; }
  @media (max-width: 39.99rem) {
    .detail { max-height: 58%; padding: 0.75rem 0.85rem 0.85rem; }
    .detail-name { font-size: 1.35rem; }
    .type-tag { font-size: 1.15rem; }
    .detail-head { margin-bottom: 0.5rem; }
    .axes { gap: 0.35rem; }
    .axis { font-size: 0.78rem; }
  }
  .bar { position: relative; height: 0.9rem; }
  .bar::before { content: ""; position: absolute; left: 0; right: 0; top: 50%; border-top: 1px solid var(--rule); }
  .bar::after { content: ""; position: absolute; left: 50%; top: 0.15rem; bottom: 0.15rem; border-left: 1px solid var(--ink-3); }
  .bar .fill { position: absolute; top: calc(50% - 2px); height: 4px; background: var(--c); }
  .bar .mark {
    position: absolute; top: 50%; width: 0.6rem; height: 0.6rem; border-radius: 50%;
    translate: -50% -50%; background: var(--c); box-shadow: 0 0 0 2px var(--paper);
  }

  /* Colour key */
  .key { margin-top: 0.85rem; }
  .key-cap { font-size: 0.8125rem; color: var(--ink-2); margin-bottom: 0.45rem; max-width: 46rem; }
  .key-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 2px; max-width: 34rem; }
  @media (min-width: 60rem) { .key-grid { grid-template-columns: repeat(8, minmax(0, 1fr)); max-width: none; } }
  .key-cell {
    min-height: 2.5rem;
    display: flex; align-items: center; gap: 0.35rem;
    padding: 0.25rem 0.4rem;
    font-family: var(--font-display);
    font-size: 0.875rem;
    letter-spacing: 0.04em;
    border: 1px solid transparent;
    border-radius: 2px;
  }
  .key-cell small { font-family: var(--font-ui); font-size: 0.75rem; color: var(--ink-3); letter-spacing: 0; margin-left: auto; }
  .key-cell:hover:not(:disabled) { border-color: var(--rule); }
  .key-cell[aria-pressed="true"] { border-color: var(--ink); background: var(--paper); }
  .key-cell:disabled { opacity: 0.35; cursor: default; }

  /* ---------- Notes column ---------- */
  .notes { padding: 1.25rem var(--gutter) 2rem; }
  @media (min-width: 60rem) { .notes { padding: 1.1rem 1.5rem 2rem; } }
  .notes h2 {
    font-family: var(--font-display); font-weight: 400;
    font-size: 1.5rem; line-height: 1.15;
    margin-bottom: 0.25rem;
  }
  .notes .sub { font-size: 0.875rem; color: var(--ink-2); margin-bottom: 0.75rem; }
  .arch-list { list-style: none; padding: 0; border-top: 1px solid var(--ink); }
  .arch { border-bottom: 1px solid var(--rule); }
  .arch.active { background: var(--seal-wash); }
  .arch-head {
    width: 100%;
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    column-gap: 0.75rem;
    align-items: baseline;
    padding: 0.85rem 0.5rem 0.2rem;
  }
  .arch-type { display: inline-flex; align-items: center; gap: 0.35rem; font-family: var(--font-display); font-size: 0.9375rem; letter-spacing: 0.06em; color: var(--ink-2); }
  .arch-name { font-family: var(--font-display); font-size: 1.2rem; line-height: 1.2; color: var(--ink); }
  .arch-head:hover .arch-name { text-decoration: underline; text-decoration-color: var(--seal); text-underline-offset: 0.15em; }
  .arch-count { grid-column: 2; font-size: 0.8125rem; color: var(--ink-3); margin-top: 0.1rem; }
  .arch-body { padding: 0.35rem 0.5rem 0.9rem; font-size: 0.9375rem; color: var(--ink-2); }
  .arch-desc { text-wrap: pretty; }
  .arch:not(.active) .arch-desc {
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
  }
  .arch-more { display: none; }
  .arch.active .arch-more { display: block; }
  .arch-themes { list-style: none; padding: 0; margin: 0.75rem 0; font-family: var(--font-display); font-style: italic; color: var(--ink); }
  .arch-themes li::before { content: "§ "; color: var(--seal); font-style: normal; }
  .members-label { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink-2); margin-bottom: 0.25rem; }
  .members { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: 0 0.1rem; }
  .members button {
    min-height: 2.25rem; padding: 0 0.4rem;
    font-size: 0.875rem; color: var(--ink);
    text-decoration: underline; text-decoration-color: var(--rule); text-underline-offset: 0.2em;
  }
  .members button:hover { text-decoration-color: var(--seal); }

  .glossary { margin-top: 1.75rem; border-top: 1px solid var(--ink); }
  .glossary summary {
    min-height: var(--tap);
    display: flex; align-items: center; gap: 0.5rem;
    font-weight: 600; font-size: 0.9375rem;
    cursor: pointer; list-style: none;
    padding: 0.5rem 0;
  }
  .glossary summary::-webkit-details-marker { display: none; }
  .glossary summary::before { content: "+"; font-family: var(--font-display); color: var(--seal); width: 1rem; font-size: 1.2rem; }
  .glossary[open] summary::before { content: "–"; }
  .glossary dl { display: grid; gap: 0.9rem; padding-bottom: 0.5rem; }
  .glossary dt { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink-2); }
  .glossary dd { font-size: 0.875rem; color: var(--ink-2); margin-top: 0.15rem; }
  .glossary dd b { font-family: var(--font-display); color: var(--seal); margin-right: 0.3rem; }
  .glossary dd strong { color: var(--ink); font-weight: 600; }

  .colophon {
    margin-top: 1.75rem; padding-top: 0.9rem;
    border-top: 3px double var(--ink);
    font-size: 0.8125rem; color: var(--ink-2);
    display: grid; gap: 0.6rem;
  }
  .colophon a { color: var(--ink); text-decoration-color: var(--rule); text-underline-offset: 0.18em; }
  .colophon a:hover { text-decoration-color: var(--seal); }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition-duration: 0.01ms !important; }
  }
</style>
</head>
<body>
<header class="masthead">
  <p class="kicker">An unserious typology of 193 serious documents</p>
  <h1>The Constitutional <em>Personality</em> Map</h1>
  <p class="dek">Every national constitution, scored on four personality axes, clustered into archetypes and given a Myers–Briggs type. Pick a lens, then find your country.</p>
</header>

<nav class="lenses" aria-label="Lens">
  <div class="lens-row" id="lens-row" role="group" aria-label="Choose a lens"></div>
</nav>
<p class="lens-dek" id="lens-dek"></p>

<main class="layout">
  <section class="stage" aria-label="Map">
    <div class="finder">
      <div class="search">
        <label for="search">Find a country</label>
        <input id="search" type="search" list="country-names" autocomplete="off" spellcheck="false" placeholder="e.g. Czech Republic" enterkeyhint="search">
        <datalist id="country-names"></datalist>
      </div>
      <div class="status" id="status" aria-live="polite"></div>
    </div>
    <div class="map" id="map">
      <canvas id="chart" role="img" aria-label="Map of 193 constitutions; nearby dots have similar personality scores. Use the search box or the archetype list to explore."></canvas>
      <p class="hint" id="hint"></p>
      <div class="zoom" role="group" aria-label="Zoom">
        <button type="button" id="zoom-in" aria-label="Zoom in">+</button>
        <button type="button" id="zoom-out" aria-label="Zoom out">−</button>
        <button type="button" id="zoom-fit" aria-label="Fit all countries">
          <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M2 6V2h4M12 2h4v4M16 12v4h-4M6 16H2v-4"/></svg>
        </button>
      </div>
      <section class="detail" id="detail" hidden aria-live="polite" aria-label="Selected country"></section>
    </div>
    <div class="key">
      <p class="key-cap">Dot colour is each country’s own type: <strong>warm = E</strong>, <strong>cool = I</strong>; vivid = N, muted = S; dark = J, light = P.<span id="key-untyped"></span> Tap a type to isolate it.</p>
      <div class="key-grid" id="key-grid" role="group" aria-label="Filter by type"></div>
    </div>
  </section>

  <aside class="notes" aria-label="Archetypes">
    <h2 id="arch-title">Archetypes</h2>
    <p class="sub">Clusters of constitutions that scored alike. Select one to light it up on the map.</p>
    <ol class="arch-list" id="arch-list"></ol>

    <details class="glossary" id="glossary">
      <summary>What the four letters mean in this lens</summary>
      <dl id="glossary-list"></dl>
    </details>

    <footer class="colophon">
      <p><strong>Method.</strong> Claude read each constitution and scored it from −1 to +1 on four axes per lens. Constitutions with similar scores sit close together on the map (UMAP); archetypes are the clusters on that map (HDBSCAN), named by Claude. Treat it as a parlour game with footnotes.</p>
      <p>Built by <a href="https://simonpodhajsky.com">Simon Podhajský</a> &amp; Claude. Inspired by <a href="https://www.linkedin.com/in/gwynethwindflower/">Gwyneth Windflower</a> asking “what if constitutions had MBTI types?” Texts from the <a href="https://constituteproject.org">Constitute Project</a>.</p>
    </footer>
  </aside>
</main>

<script>
const LENSES = __LENSES_JSON__;
const LENS_IDS = Object.keys(LENSES);
const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
const AXES = ['E_I', 'S_N', 'T_F', 'J_P'];
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const COARSE = matchMedia('(pointer: coarse)').matches;

// E warm / I cool by hue; N vivid / S muted by chroma; J dark / P light by lightness.
const HUE = { IST: 245, ISF: 185, INT: 278, INF: 320, EST: 80, ESF: 52, ENT: 30, ENF: 4 };
function typeColor(t) {
  if (!/^[EI][SN][TF][JP]$/.test(t)) return 'oklch(62% 0 0)';
  const n = t[1] === 'N', j = t[3] === 'J';
  return `oklch(${j ? 46 : 63}% ${n ? 0.16 : 0.085} ${HUE[t.slice(0, 3)]})`;
}

const esc = s => String(s ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
const md = s => esc(s).replace(/\*([^*]+)\*/g, '<em>$1</em>');
const fmt = v => (v >= 0 ? '+' : '−') + Math.abs(v).toFixed(2);
const easeOut = t => 1 - Math.pow(1 - t, 4);
const $ = id => document.getElementById(id);

const state = { lens: LENS_IDS[0], selected: null, hovered: null, cluster: null, type: null, query: '', matches: null };
const lens = () => LENSES[state.lens];
const isLens = id => typeof id === 'string' && Object.hasOwn(LENSES, id);
const countries = () => lens().countries;
const byId = id => countries().find(c => c.country_id === id);

// ---------- Canvas & view ----------
const canvas = $('chart'), ctx = canvas.getContext('2d'), mapEl = $('map');
let W = 0, H = 0, dpr = 1;
let view = { x: 0, y: 0, k: 1 }, fitK = 1;
let posTween = null;   // lens change: screen positions animate old -> new
let viewTween = null;  // zoom/pan animations
let raf = 0;

function requestDraw() { if (!raf) raf = requestAnimationFrame(frame); }
function frame(now) {
  raf = 0;
  if (viewTween) {
    const t = Math.min(1, (now - viewTween.start) / viewTween.dur), e = easeOut(t);
    for (const k of ['x', 'y', 'k']) view[k] = viewTween.from[k] + (viewTween.to[k] - viewTween.from[k]) * e;
    if (t >= 1) viewTween = null;
  }
  if (posTween && now - posTween.start >= posTween.dur) posTween = null;
  draw(now);
  updateTouchMode();
  if (viewTween || posTween) requestDraw();
}

function resize() {
  const r = mapEl.getBoundingClientRect();
  dpr = Math.min(window.devicePixelRatio || 1, 2.5);
  W = r.width; H = r.height;
  canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function fitView() {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const c of countries()) { x0 = Math.min(x0, c.x); x1 = Math.max(x1, c.x); y0 = Math.min(y0, c.y); y1 = Math.max(y1, c.y); }
  const padTop = 44, padSide = W < 640 ? 24 : 56, padRight = padSide + 44;
  const k = Math.min((W - padSide - padRight) / (x1 - x0 || 1), (H - padTop - padSide) / (y1 - y0 || 1));
  return { k, x: padSide + (W - padSide - padRight - (x1 - x0) * k) / 2 - x0 * k, y: padTop + (H - padTop - padSide - (y1 - y0) * k) / 2 - y0 * k };
}
function animateView(to, dur = 450) {
  if (REDUCED) { view = { ...to }; viewTween = null; requestDraw(); return; }
  viewTween = { from: { ...view }, to, start: performance.now(), dur };
  requestDraw();
}
function zoomAt(factor, cx, cy, animate) {
  const k = Math.max(fitK * 0.5, Math.min(fitK * 40, view.k * factor));
  const f = k / view.k;
  const to = { k, x: cx - (cx - view.x) * f, y: cy - (cy - view.y) * f };
  if (animate) animateView(to, 300); else { view = to; requestDraw(); }
}
function updateTouchMode() {
  // At fit zoom a one-finger swipe scrolls the page; once zoomed in it pans the map.
  canvas.style.touchAction = view.k > fitK * 1.05 ? 'none' : 'pan-y';
}

function screenPositions(now) {
  const pts = countries().map(c => ({ x: c.x * view.k + view.x, y: c.y * view.k + view.y }));
  if (posTween) {
    const e = easeOut(Math.min(1, (now - posTween.start) / posTween.dur));
    countries().forEach((c, i) => {
      const from = posTween.from.get(c.country_id);
      if (from) pts[i] = { x: from.x + (pts[i].x - from.x) * e, y: from.y + (pts[i].y - from.y) * e };
    });
  }
  return pts;
}
let lastPts = [];

function isLit(c) {
  return (state.cluster === null || String(c.cluster) === state.cluster)
    && (state.type === null || c.mbti === state.type)
    && (!state.matches || state.matches.has(c.country_id));
}

const css = getComputedStyle(document.documentElement);
const PAPER = css.getPropertyValue('--paper').trim();
const INK = css.getPropertyValue('--ink').trim();
const SEAL = css.getPropertyValue('--seal').trim();

function draw(now = performance.now()) {
  ctx.clearRect(0, 0, W, H);
  const cs = countries();
  const pts = lastPts = screenPositions(now);
  const zoomGain = Math.min(1.7, Math.sqrt(view.k / fitK));
  const r = (COARSE ? 5.5 : 4.75) * Math.max(1, zoomGain);
  const filtering = state.cluster !== null || state.type !== null || state.matches;

  // Dimmed points first, so lit ones sit on top.
  for (const pass of [false, true]) {
    for (let i = 0; i < cs.length; i++) {
      const lit = isLit(cs[i]);
      if (lit !== pass) continue;
      ctx.globalAlpha = lit ? 1 : 0.16;
      ctx.beginPath();
      ctx.arc(pts[i].x, pts[i].y, r, 0, Math.PI * 2);
      ctx.fillStyle = typeColor(cs[i].mbti);
      ctx.fill();
      if (lit) { ctx.lineWidth = 1.25; ctx.strokeStyle = PAPER; ctx.stroke(); }
    }
  }
  ctx.globalAlpha = 1;

  const ring = (id, color, extra, width) => {
    const i = cs.findIndex(c => c.country_id === id);
    if (i < 0) return;
    ctx.beginPath(); ctx.arc(pts[i].x, pts[i].y, r + extra, 0, Math.PI * 2);
    ctx.lineWidth = width; ctx.strokeStyle = color; ctx.stroke();
  };
  if (state.hovered && state.hovered !== state.selected) ring(state.hovered, INK, 2.5, 1.5);
  if (state.selected) ring(state.selected, SEAL, 3.5, 2.25);

  // Labels: selected and hovered always; then search hits; then everything once zoomed in. Greedy de-overlap.
  const order = [];
  const push = (i, strong) => { if (i >= 0 && !order.some(o => o.i === i)) order.push({ i, strong }); };
  push(cs.findIndex(c => c.country_id === state.selected), true);
  push(cs.findIndex(c => c.country_id === state.hovered), true);
  if (state.matches && state.matches.size <= 40) cs.forEach((c, i) => { if (isLit(c)) push(i, false); });
  if (view.k >= fitK * 2.4 || (filtering && !state.matches && cs.filter(isLit).length <= 12)) {
    cs.forEach((c, i) => { if (isLit(c)) push(i, false); });
  }
  const boxes = [];
  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.lineJoin = 'round';
  for (const { i, strong } of order) {
    const p = pts[i];
    if (p.x < -50 || p.x > W + 50 || p.y < -20 || p.y > H + 20) continue;
    ctx.font = `${strong ? 700 : 500} ${strong ? 14 : 12}px "Public Sans", system-ui, sans-serif`;
    const w = ctx.measureText(cs[i].country).width, h = strong ? 15 : 13;
    let y = p.y - r - 7;
    let box = { x0: p.x - w / 2 - 3, x1: p.x + w / 2 + 3, y0: y - h, y1: y + 3 };
    const hits = b => boxes.some(o => b.x0 < o.x1 && b.x1 > o.x0 && b.y0 < o.y1 && b.y1 > o.y0);
    if (hits(box) && !strong) {
      y = p.y + r + h + 4;
      box = { ...box, y0: y - h, y1: y + 3 };
      if (hits(box)) continue;
    }
    boxes.push(box);
    ctx.lineWidth = 4; ctx.strokeStyle = PAPER; ctx.strokeText(cs[i].country, p.x, y);
    ctx.fillStyle = INK; ctx.fillText(cs[i].country, p.x, y);
  }
}

function nearest(mx, my) {
  const radius = COARSE ? 26 : 14;
  let best = -1, bestD = radius;
  lastPts.forEach((p, i) => {
    // Prefer lit points: dimmed ones need to be much closer to win.
    const d = Math.hypot(p.x - mx, p.y - my) * (isLit(countries()[i]) ? 1 : 1.8);
    if (d < bestD) { bestD = d; best = i; }
  });
  return best;
}

// ---------- Pointer interaction ----------
const pointers = new Map();
let drag = null, pinch = null;
const local = e => { const r = canvas.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; };

canvas.addEventListener('pointerdown', e => {
  const p = local(e);
  pointers.set(e.pointerId, p);
  canvas.setPointerCapture(e.pointerId);
  if (pointers.size === 1) drag = { start: p, last: p, moved: false };
  if (pointers.size === 2) {
    const [a, b] = [...pointers.values()];
    pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), cx: (a.x + b.x) / 2, cy: (a.y + b.y) / 2 };
    drag = null;
  }
  viewTween = null;
});
canvas.addEventListener('pointermove', e => {
  const p = local(e);
  if (!pointers.has(e.pointerId)) {
    if (e.pointerType === 'mouse') {
      const i = nearest(p.x, p.y);
      const id = i >= 0 ? countries()[i].country_id : null;
      canvas.classList.toggle('on-point', !!id);
      if (id !== state.hovered) { state.hovered = id; requestDraw(); }
    }
    return;
  }
  pointers.set(e.pointerId, p);
  if (pinch && pointers.size >= 2) {
    const [a, b] = [...pointers.values()];
    const d = Math.hypot(a.x - b.x, a.y - b.y), cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2;
    view.x += cx - pinch.cx; view.y += cy - pinch.cy;
    zoomAt(d / (pinch.d || d), cx, cy, false);
    pinch = { d, cx, cy };
    requestDraw();
  } else if (drag) {
    if (!drag.moved && Math.hypot(p.x - drag.start.x, p.y - drag.start.y) > 5) {
      drag.moved = true; canvas.classList.add('dragging'); hideHint();
    }
    if (drag.moved) { view.x += p.x - drag.last.x; view.y += p.y - drag.last.y; requestDraw(); }
    drag.last = p;
  }
});
function endPointer(e, cancelled) {
  const p = local(e);
  if (!cancelled && drag && !drag.moved && pointers.size === 1) {
    const i = nearest(p.x, p.y);
    if (i >= 0) select(countries()[i].country_id, { center: false });
    else if (state.selected) select(null);
  }
  pointers.delete(e.pointerId);
  if (pointers.size < 2) pinch = null;
  if (pointers.size === 0) drag = null;
  else if (pointers.size === 1) { const [q] = [...pointers.values()]; drag = { start: q, last: q, moved: true }; }
  canvas.classList.remove('dragging');
}
canvas.addEventListener('pointerup', e => endPointer(e, false));
canvas.addEventListener('pointercancel', e => endPointer(e, true));
canvas.addEventListener('pointerleave', e => {
  if (e.pointerType === 'mouse' && state.hovered) { state.hovered = null; canvas.classList.remove('on-point'); requestDraw(); }
});
canvas.addEventListener('wheel', e => {
  e.preventDefault();
  const p = local(e);
  zoomAt(Math.exp(-e.deltaY * (e.deltaMode === 1 ? 0.05 : 0.0018)), p.x, p.y, false);
  hideHint();
}, { passive: false });

$('zoom-in').onclick = () => { zoomAt(1.6, W / 2, H / 2, true); hideHint(); };
$('zoom-out').onclick = () => zoomAt(1 / 1.6, W / 2, H / 2, true);
$('zoom-fit').onclick = () => animateView(fitView());

const hint = $('hint');
hint.textContent = COARSE ? 'Tap a dot · pinch or + to zoom' : 'Click a dot · drag to pan · scroll to zoom';
function hideHint() { hint.classList.add('gone'); }

// ---------- Selection & filters ----------
function select(id, { center = true } = {}) {
  state.selected = id;
  renderDetail();
  if (id && center) revealSelected(true);
  else if (id) keepClearOfPanel();
  hideHint();
  syncHash();
  requestDraw();
}
function freeSpot() {
  // Centre of the part of the map not covered by the detail panel (or by the bottom of the window).
  const mr = mapEl.getBoundingClientRect();
  const visH = Math.max(160, Math.min(H, innerHeight - Math.max(0, mr.top)));
  const panel = $('detail');
  if (panel.hidden) return { x: W / 2, y: visH / 2 };
  const pr = panel.getBoundingClientRect();
  if (pr.top - mr.top < H / 3) {           // panel pinned top-left (wide screens)
    const left = pr.right - mr.left;
    return { x: left + (W - left) / 2, y: visH / 2 };
  }
  return { x: W / 2, y: Math.max(60, (pr.top - mr.top) / 2) };  // panel along the bottom (phones)
}
function revealSelected(animate) {
  const c = byId(state.selected);
  if (!c) return;
  const k = Math.max(view.k, fitK * 2), spot = freeSpot();
  const to = { k, x: spot.x - c.x * k, y: spot.y - c.y * k };
  if (animate) animateView(to, 550); else { view = to; viewTween = null; requestDraw(); }
}
function keepClearOfPanel() {
  // After a tap, move the map only if the chosen dot ended up under the detail panel.
  const i = countries().findIndex(c => c.country_id === state.selected);
  const p = lastPts[i];
  if (!p) return;
  const pr = $('detail').getBoundingClientRect(), mr = mapEl.getBoundingClientRect();
  const x0 = pr.left - mr.left - 16, x1 = pr.right - mr.left + 16, y0 = pr.top - mr.top - 16, y1 = pr.bottom - mr.top + 16;
  if (p.x > x0 && p.x < x1 && p.y > y0 && p.y < y1) {
    const spot = freeSpot();
    animateView({ ...view, x: view.x + spot.x - p.x, y: view.y + spot.y - p.y }, 400);
  }
}
function frameLit() {
  // Zoom to whatever the filters leave lit; back out to everything when nothing is filtered.
  const lit = countries().filter(isLit);
  if (!lit.length || lit.length === countries().length) { animateView(fitView()); return; }
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const c of lit) { x0 = Math.min(x0, c.x); x1 = Math.max(x1, c.x); y0 = Math.min(y0, c.y); y1 = Math.max(y1, c.y); }
  const pad = 70;
  const k = Math.min(fitK * 4, (W - 2 * pad) / Math.max(x1 - x0, 1e-6), (H - 2 * pad) / Math.max(y1 - y0, 1e-6));
  const spot = { x: W / 2, y: Math.min(H, innerHeight - Math.max(0, mapEl.getBoundingClientRect().top)) / 2 };
  animateView({ k, x: spot.x - (x0 + x1) / 2 * k, y: Math.max(pad, spot.y) - (y0 + y1) / 2 * k }, 600);
}
function refreshFilters() {
  renderArchetypes(); renderKey(); renderStatus(); frameLit(); requestDraw();
}
// Search, archetype and type filters are mutually exclusive: one question at a time.
function clearSearch() { state.query = ''; state.matches = null; search.value = ''; }
function setCluster(cid) {
  state.cluster = state.cluster === cid ? null : cid;
  state.type = null; clearSearch();
  refreshFilters();
}
function setType(t) {
  state.type = state.type === t ? null : t;
  state.cluster = null; clearSearch();
  refreshFilters();
}
function clearFilters() {
  state.cluster = null; state.type = null; clearSearch();
  refreshFilters();
}

// ---------- Search ----------
const search = $('search');
const hay = c => (c.country + ' ' + c.country_id.replace(/_+/g, ' ')).toLowerCase();
function pickFromSearch(id) {
  // The panel now names the country, so drop the search highlight.
  clearSearch(); renderStatus();
  select(id); search.blur();
}
function runSearch(q) {
  if (q.trim() && (state.cluster !== null || state.type !== null)) {
    state.cluster = null; state.type = null; renderArchetypes(); renderKey();
  }
  state.query = q.trim().toLowerCase();
  state.matches = state.query ? new Set(countries().filter(c => hay(c).includes(state.query)).map(c => c.country_id)) : null;
  renderStatus(); requestDraw();
}
search.addEventListener('input', e => {
  runSearch(search.value);
  // Picking from the datalist fills the exact name: select it straight away.
  const exact = countries().find(c => c.country.toLowerCase() === state.query);
  if (exact && (!e.inputType || e.inputType === 'insertReplacementText')) pickFromSearch(exact.country_id);
});
search.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    e.preventDefault();
    const hit = countries().find(c => state.matches?.has(c.country_id) && isLit(c));
    if (hit) pickFromSearch(hit.country_id);
  } else if (e.key === 'Escape') { search.value = ''; runSearch(''); }
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && state.selected && document.activeElement !== search) select(null);
});

// ---------- Rendering: DOM ----------
function renderLensButtons() {
  $('lens-row').innerHTML = LENS_IDS.map((id, n) => `
    <button type="button" class="lens-btn" data-lens="${esc(id)}" aria-pressed="${id === state.lens}">
      <span class="art">Art. ${ROMAN[n]}</span><span>${esc(LENSES[id].name)}</span>
    </button>`).join('');
  $('lens-row').querySelectorAll('.lens-btn').forEach(b => b.onclick = () => switchLens(b.dataset.lens));
}

function renderDetail() {
  const el = $('detail');
  const c = state.selected && byId(state.selected);
  if (!c) { el.hidden = true; return; }
  const l = lens(), arch = l.archetypes[String(c.cluster)] || { name: 'Unclustered' };
  const color = typeColor(c.mbti);
  const rows = AXES.map((key, n) => {
    const [a, b] = key.split('_'), dim = l.dimensions[key] || {};
    const v = Math.max(-1, Math.min(1, c.scores?.[key] ?? 0));
    const mark = 50 - v * 50;
    const letter = c.mbti[n];
    return `<li class="axis">
      <span class="pole${letter === a ? ' on' : ''}"><b>${a}</b>${esc(dim[a + '_label'])}</span>
      <span class="bar" role="img" aria-label="${esc(dim.name || key)}: ${fmt(v)}, toward ${esc(v >= 0 ? dim[a + '_label'] : dim[b + '_label'])}">
        <span class="fill" style="left:${Math.min(50, mark)}%;width:${Math.abs(mark - 50)}%"></span>
        <span class="mark" style="left:${mark}%"></span>
      </span>
      <span class="pole right${letter === b ? ' on' : ''}">${esc(dim[b + '_label'])}<b>${b}</b></span>
    </li>`;
  }).join('');
  el.style.setProperty('--c', color);
  el.innerHTML = `
    <button type="button" class="detail-close" aria-label="Close">×</button>
    <p class="detail-arch"><button type="button" data-cid="${esc(c.cluster)}">${esc(arch.name)}</button></p>
    <div class="detail-head">
      <h2 class="detail-name">${esc(c.country)}</h2>
      <span class="type-tag"><span class="sw"></span>${esc(c.mbti)}</span>
    </div>
    <ol class="axes">${rows}</ol>`;
  el.hidden = false;
  el.querySelector('.detail-close').onclick = () => select(null);
  el.querySelector('.detail-arch button').onclick = () => {
    const cid = String(c.cluster);
    if (state.cluster !== cid) setCluster(cid);
    document.querySelector(`.arch[data-cid="${CSS.escape(cid)}"]`)?.scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'nearest' });
  };
}

function renderStatus() {
  const el = $('status'), cs = countries(), lit = cs.filter(isLit).length;
  const parts = [];
  if (state.cluster !== null) parts.push(esc(lens().archetypes[state.cluster]?.name));
  if (state.type) parts.push(esc(state.type));
  if (state.matches) parts.push(`“${esc(search.value.trim())}”`);
  if (!parts.length) { el.innerHTML = `<span><strong>${cs.length}</strong> constitutions</span>`; return; }
  el.innerHTML = lit
    ? `<span><strong>${lit}</strong> of ${cs.length} · ${parts.join(' · ')}</span><button type="button" class="link-btn" id="clear">Clear</button>`
    : `<span>No country matches ${parts.join(' · ')}</span><button type="button" class="link-btn" id="clear">Clear</button>`;
  $('clear').onclick = clearFilters;
}

function renderKey() {
  const counts = {};
  countries().forEach(c => counts[c.mbti] = (counts[c.mbti] || 0) + 1);
  const types = [];
  for (const row of ['IS', 'IN', 'ES', 'EN']) for (const col of ['TJ', 'TP', 'FJ', 'FP']) types.push(row[0] + row[1] + col[0] + col[1]);
  $('key-grid').innerHTML = types.map(t => `
    <button type="button" class="key-cell" data-type="${t}" aria-pressed="${state.type === t}" ${counts[t] ? '' : 'disabled'}
      aria-label="${t}, ${counts[t] || 0} countries">
      <span class="sw" style="--c:${typeColor(t)}"></span>${t}<small>${counts[t] || ''}</small>
    </button>`).join('');
  $('key-grid').querySelectorAll('.key-cell').forEach(b => b.onclick = () => setType(b.dataset.type));
  const untyped = countries().filter(c => !/^[EI][SN][TF][JP]$/.test(c.mbti)).length;
  $('key-untyped').textContent = untyped ? ` Grey = no type assigned (${untyped}).` : '';
}

function renderArchetypes() {
  const l = lens(), cs = countries();
  $('arch-title').textContent = `${l.archetypes ? Object.keys(l.archetypes).length : 0} archetypes`;
  const ids = Object.keys(l.archetypes).sort((a, b) => cs.filter(c => String(c.cluster) === b).length - cs.filter(c => String(c.cluster) === a).length);
  $('arch-list').innerHTML = ids.map(cid => {
    const a = l.archetypes[cid];
    const members = cs.filter(c => String(c.cluster) === cid).sort((x, y) => x.country.localeCompare(y.country));
    const active = state.cluster === cid;
    return `<li class="arch${active ? ' active' : ''}" data-cid="${esc(cid)}">
      <button type="button" class="arch-head" aria-pressed="${active}" aria-expanded="${active}">
        <span class="arch-type"><span class="sw" style="--c:${typeColor(a.mbti)}"></span>${esc(a.mbti)}</span>
        <span class="arch-name">${esc(a.name)}</span>
        <span class="arch-count">${members.length} ${members.length === 1 ? 'country' : 'countries'}</span>
      </button>
      <div class="arch-body">
        <p class="arch-desc">${md(a.description)}</p>
        <div class="arch-more">
          ${a.key_themes?.length ? `<ul class="arch-themes">${a.key_themes.map(t => `<li>${md(t)}</li>`).join('')}</ul>` : ''}
          <p class="members-label">Members</p>
          <ul class="members">${members.map(m => `<li><button type="button" data-id="${esc(m.country_id)}">${esc(m.country)}</button></li>`).join('')}</ul>
        </div>
      </div>
    </li>`;
  }).join('');
  $('arch-list').querySelectorAll('.arch-head').forEach(b => b.onclick = () => setCluster(b.parentElement.dataset.cid));
  $('arch-list').querySelectorAll('.members button').forEach(b => b.onclick = () => {
    select(b.dataset.id);
    if (matchMedia('(max-width: 59.99rem)').matches) mapEl.scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'center' });
  });
}

function renderGlossary() {
  const l = lens();
  $('glossary-list').innerHTML = AXES.map(key => {
    const [a, b] = key.split('_'), d = l.dimensions[key] || {};
    return `<div><dt>${a} / ${b}${d.name ? ' · ' + esc(d.name) : ''}</dt>
      <dd><b>${a}</b><strong>${esc(d[a + '_label'])}</strong>: ${esc(d[a + '_desc'])}</dd>
      <dd><b>${b}</b><strong>${esc(d[b + '_label'])}</strong>: ${esc(d[b + '_desc'])}</dd></div>`;
  }).join('');
}

function renderLensText() {
  const n = LENS_IDS.indexOf(state.lens);
  $('lens-dek').textContent = `Article ${ROMAN[n]}: ${lens().description}`;
  $('country-names').innerHTML = [...countries()].sort((a, b) => a.country.localeCompare(b.country)).map(c => `<option value="${esc(c.country)}">`).join('');
}

function switchLens(id, { animate = true } = {}) {
  if (!isLens(id)) return;
  const from = new Map(countries().map((c, i) => [c.country_id, lastPts[i]]).filter(([, p]) => p));
  state.lens = id;
  state.cluster = null; state.type = null; state.hovered = null;
  if (state.selected && !byId(state.selected)) state.selected = null;
  if (state.query) runSearch(search.value);
  const fit = fitView();
  fitK = fit.k; view = fit; viewTween = null;
  posTween = animate && !REDUCED && from.size ? { from, start: performance.now(), dur: 750 } : null;
  renderLensButtons(); renderLensText(); renderArchetypes(); renderKey(); renderGlossary(); renderStatus(); renderDetail();
  syncHash();
  requestDraw();
}

// ---------- Shareable URL: #lens=vibes&country=Czech_Republic_the ----------
function syncHash() {
  const p = new URLSearchParams({ lens: state.lens });
  if (state.selected) p.set('country', state.selected);
  history.replaceState(null, '', '#' + p.toString());
}
function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  return { lens: p.get('lens'), country: p.get('country') };
}

// ---------- Boot ----------
resize();
const initial = readHash();
switchLens(isLens(initial.lens) ? initial.lens : state.lens, { animate: false });
if (initial.country && byId(initial.country)) {
  select(initial.country);
  if (matchMedia('(max-width: 59.99rem)').matches) mapEl.scrollIntoView({ block: 'center' });
}
let lastSize = '';
new ResizeObserver(() => {
  const size = Math.round(mapEl.clientWidth) + 'x' + Math.round(mapEl.clientHeight);
  if (size === lastSize) return;
  lastSize = size;
  resize();
  const fit = fitView(); fitK = fit.k;
  if (state.selected) revealSelected(false); else { view = fit; viewTween = null; }
  requestDraw();
}).observe(mapEl);
document.fonts?.ready.then(requestDraw);
</script>
</body>
</html>
"""


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
                    "country": display_name(a["country_id"]),
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
