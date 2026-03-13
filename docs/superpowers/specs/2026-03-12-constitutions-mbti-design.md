# Constitutional Personality Archetypes — Design Spec

## Context

Inspired by a LinkedIn exchange between Simon Podhajský and Gwyneth Windflower about synthesizing all national constitutions into a personality archetype system ("The Czech Constitution seems like an INTJ", "the US Constitution is unfortunately an ENFP vision board"). The goal is to collect the world's constitutions, cluster them by structural and thematic similarity, discover natural archetypes, and map them to MBTI types as a fun, shareable lens.

## Goal

Build a Python pipeline that:
1. Collects ~200 national constitutions from the Constitute Project
2. Extracts topic-level structured features using their standardized tagging
3. Embeds topic sections using a configurable embedding provider (via OpenRouter)
4. Clusters constitutions to discover natural groupings
5. Uses Claude to name archetypes, describe them, and assign MBTI types
6. Produces a 2D UMAP visualization and a structured JSON dataset

## Architecture

### Step 1: Data Collection (`src/collect.py`)

- **Source**: Constitute Project (constituteproject.org) only
- **Method**: The Constitute Project provides a public API at `https://www.constituteproject.org/api/`. Use their API endpoints to fetch constitution texts and topic annotations. If the API is unavailable or insufficient, fall back to scraping the HTML pages with polite rate limiting (1 request/second, respect robots.txt).
- **Storage**: JSON files in `data/raw/`, one per country
- **Schema per file**:
  ```json
  {
    "country": "Czech Republic",
    "country_code": "CZE",
    "year_adopted": 1993,
    "year_amended": 2013,
    "full_text": "...",
    "topics": {
      "judicial_independence": "Section text...",
      "right_to_health_care": "Section text...",
      ...
    }
  }
  ```
- **Target**: All available constitutions (~190-200 countries)

### Step 2: Feature Extraction (`src/extract.py`)

- Parse Constitute Project's ~70+ standardized topics per constitution
- Build two feature types:
  - **Binary presence**: which topics each constitution addresses (70+ dimensions)
  - **Semantic content**: the actual text of each topic section (for embedding)
- Output: structured JSON in `data/processed/` with both feature types
- Handle missing topics gracefully (many constitutions won't cover all 70+ topics)

### Step 3: Embedding (`src/embed.py`)

- **Configurable backend** via OpenRouter — user can swap embedding models without code changes
- **Config** in `src/config.py`: model name, API base URL, API key (from env var)
- **Default**: A good general-purpose embedding model available via OpenRouter
- **Process**: Embed each topic section text → average all topic embeddings to get a single per-country embedding vector (averaging is simpler and works well when topic counts vary across countries)
- **Combine**: Concatenate binary topic features + semantic embeddings into a unified feature vector per country
- **Cache**: Save embeddings to `data/processed/embeddings.npz` to avoid re-computing

### Step 4: Clustering (`src/cluster.py`)

- **Random seed**: Use a fixed seed (42) for UMAP and HDBSCAN for reproducible results
- **Dimensionality reduction**: UMAP to reduce the combined feature space
  - 2D projection for visualization
  - Higher-dimensional (~10-20D) projection for clustering
- **Clustering**: HDBSCAN on the higher-dimensional UMAP projection
  - Density-based: discovers natural cluster count (no need to specify k)
  - Target: ~8-16 clusters as archetype candidates
  - Noise points (HDBSCAN label -1): assign to nearest cluster centroid but flag as "borderline" in the output
- **Output**: Cluster assignments per country, saved to `data/results/clusters.json`

### Step 5: Archetype Generation (`src/archetypes.py`)

- For each cluster, select 3-5 representative constitutions (closest to centroid)
- Send to Claude (claude-sonnet-4-6, sufficient for this analytical task) via Anthropic API:
  - Provide the **topic sections only** (not full text) for representative constitutions — keeps within context limits and is more relevant than raw full text
  - Name the archetype (evocative: "The Guardian State", "The Social Contract", etc.)
  - Describe what values, structures, and priorities define it
  - Assign an MBTI type with reasoning
- For every country: assign archetype + MBTI type + brief rationale
- **Output**: `data/results/archetypes.json` with per-cluster and per-country results

### Step 6: Visualization (`src/visualize.py`)

- Generate an interactive 2D UMAP scatter plot
- Each point = one country, colored by archetype/cluster
- Hover labels: country name, archetype, MBTI type
- Format: HTML file using Plotly (interactive, shareable, no server needed)
- Also assembles the final `outputs/typology.json` by combining cluster assignments, archetype data, and UMAP coordinates
- **Output**: `outputs/constitution_map.html` + `outputs/typology.json`

## Project Structure

```
constitutions-mbti/
├── pyproject.toml              # uv project, all dependencies
├── src/
│   ├── __init__.py
│   ├── config.py               # Embedding provider config (OpenRouter)
│   ├── collect.py              # Scrape Constitute Project
│   ├── extract.py              # Parse topics, build features
│   ├── embed.py                # Configurable embeddings via OpenRouter
│   ├── cluster.py              # UMAP + HDBSCAN clustering
│   ├── archetypes.py           # Claude archetype generation
│   └── visualize.py            # UMAP scatter plot (Plotly HTML)
├── data/
│   ├── raw/                    # Raw constitution JSONs
│   ├── processed/              # Structured features + embeddings
│   └── results/                # Clusters, archetypes, MBTI mappings
├── notebooks/
│   └── explore.ipynb           # Ad-hoc exploration
├── outputs/
│   ├── typology.json           # Final combined dataset
│   └── constitution_map.html   # Interactive UMAP visualization
└── docs/
    └── superpowers/specs/      # This spec
```

## Dependencies

- `httpx` + `beautifulsoup4` — scraping
- `numpy` + `pandas` — data handling
- `openai` — OpenRouter-compatible API client for embeddings (OpenRouter uses the OpenAI-compatible API format)
- `umap-learn` — dimensionality reduction
- `hdbscan` — density-based clustering
- `scikit-learn` — utilities (scaling, metrics)
- `plotly` — interactive visualization
- `anthropic` — Claude API for archetype generation

## Configuration

Embedding config via environment variables:
- `OPENROUTER_API_KEY` — API key for OpenRouter
- `EMBEDDING_MODEL` — model identifier (default: `openai/text-embedding-3-small` via OpenRouter)

Claude config:
- `ANTHROPIC_API_KEY` — for archetype generation step

## Output Schema

`outputs/typology.json`:
```json
{
  "archetypes": [
    {
      "id": 1,
      "name": "The Guardian State",
      "description": "Constitutions emphasizing security, order, and strong executive...",
      "mbti": "ISTJ",
      "mbti_reasoning": "...",
      "countries": ["Singapore", "..."]
    }
  ],
  "countries": [
    {
      "country": "Czech Republic",
      "country_code": "CZE",
      "archetype_id": 3,
      "archetype_name": "...",
      "mbti": "INTJ",
      "rationale": "...",
      "umap_x": 1.23,
      "umap_y": -0.45
    }
  ]
}
```

## Verification

1. **Data collection**: Run `collect.py`, verify ~190 JSON files appear in `data/raw/`, spot-check 3-5 countries for completeness
2. **Feature extraction**: Run `extract.py`, verify topic counts are reasonable (most countries should have 30-60+ topics)
3. **Embeddings**: Run `embed.py`, verify `embeddings.npz` is created and dimensionality matches expectations
4. **Clustering**: Run `cluster.py`, verify clusters are neither trivial (1 cluster) nor degenerate (190 clusters). Check that cluster sizes are reasonable.
5. **Archetypes**: Run `archetypes.py`, verify each cluster has a name, description, and MBTI type. Spot-check that assignments make intuitive sense (e.g., Scandinavian countries cluster together).
6. **Visualization**: Open `constitution_map.html` in browser, verify interactive scatter plot renders with hover labels.
7. **End-to-end**: Check `typology.json` has all ~190 countries with archetype and MBTI assignments.
