"""Score constitutions on MBTI dimensions, cluster, and generate archetypes."""

import json
import time
from pathlib import Path

import hdbscan
import numpy as np
from openai import OpenAI
from umap import UMAP

from src.config import CLAUDE_MODEL, DATA_PROCESSED, DATA_RESULTS, OPENROUTER_API_KEY, OPENROUTER_BASE_URL
from src.dimensions import DIMENSION_SETS

SEED = 42


def load_topic_texts() -> tuple[list[str], dict[str, dict[str, str]]]:
    """Load country IDs and their topic texts."""
    features = json.loads((Path(DATA_PROCESSED) / "features.json").read_text())
    countries = features["countries"]
    topic_texts = features["topic_texts"]
    return countries, topic_texts


def build_scoring_prompt(
    country_batch: list[dict],
    topic_texts: dict,
    dim_set: dict,
) -> str:
    """Build prompt to score a batch of constitutions on 4 dimensions."""
    dims = dim_set["dimensions"]

    dim_descriptions = []
    for key in ["E_I", "S_N", "T_F", "J_P"]:
        d = dims[key]
        first, second = key.split("_")
        dim_descriptions.append(
            f"**{d['name']}**: Score from -1.0 to +1.0\n"
            f"  - Negative (-1.0) = {d[f'{second}_label']}: {d[f'{second}_desc']}\n"
            f"  - Positive (+1.0) = {d[f'{first}_label']}: {d[f'{first}_desc']}"
        )
    dim_text = "\n".join(dim_descriptions)

    country_sections = []
    for c in country_batch:
        cid = c["country_id"]
        texts = topic_texts.get(cid, {})
        # Pick top 10 most substantial topics
        sorted_topics = sorted(texts.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        topic_summary = "\n".join(f"  [{k}]: {v[:200]}" for k, v in sorted_topics)
        country_sections.append(f"### {cid}\n{topic_summary}")

    countries_text = "\n\n".join(country_sections)

    return f"""Score each constitution on 4 personality dimensions. Use the topic sections provided.

## Dimension Definitions (lens: "{dim_set['name']}")
{dim_text}

## Constitutions to Score
{countries_text}

## Instructions
For each country, assign a score from -1.0 to +1.0 on each dimension. Be decisive — avoid clustering everything near 0. Use the full range.

Then assign an MBTI 4-letter type based on the scores (positive = first letter, negative = second letter for each pair: E/I, S/N, T/F, J/P).

Respond with ONLY a JSON array:
```json
[
  {{"country_id": "...", "E_I": 0.5, "S_N": -0.3, "T_F": 0.8, "J_P": -0.6, "mbti": "ENFP"}},
  ...
]
```"""


def score_all_constitutions(
    countries: list[dict],
    topic_texts: dict,
    dim_set: dict,
    client: OpenAI,
    batch_size: int = 10,
) -> list[dict]:
    """Score all constitutions on dimensions in batches."""
    all_scores = []

    for i in range(0, len(countries), batch_size):
        batch = countries[i : i + batch_size]
        batch_ids = [c["country_id"] for c in batch]
        print(f"    Scoring batch {i // batch_size + 1}/{(len(countries) + batch_size - 1) // batch_size}: {batch_ids[0]}...{batch_ids[-1]}")

        prompt = build_scoring_prompt(batch, topic_texts, dim_set)

        resp = client.chat.completions.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        text = resp.choices[0].message.content
        try:
            start = text.index("[")
            end = text.rindex("]") + 1
            scores = json.loads(text[start:end])
            all_scores.extend(scores)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"    Warning: failed to parse batch starting at {batch_ids[0]}: {e}")
            # Fill with zeros as fallback
            for c in batch:
                all_scores.append({
                    "country_id": c["country_id"],
                    "E_I": 0.0, "S_N": 0.0, "T_F": 0.0, "J_P": 0.0,
                    "mbti": "????",
                })

    return all_scores


def cluster_scores(scores: list[dict]) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """UMAP + HDBSCAN on the 4D score matrix."""
    matrix = np.array([[s["E_I"], s["S_N"], s["T_F"], s["J_P"]] for s in scores])

    # UMAP to 2D for visualization
    umap = UMAP(n_components=2, random_state=SEED, n_neighbors=15, min_dist=0.3)
    coords_2d = umap.fit_transform(matrix)

    # HDBSCAN clustering
    clusterer = hdbscan.HDBSCAN(min_cluster_size=8, min_samples=3)
    labels = clusterer.fit_predict(coords_2d)

    # Assign noise to nearest cluster
    n_noise = (labels == -1).sum()
    if n_noise > 0:
        from sklearn.metrics import pairwise_distances
        centroids = {}
        for cid in set(labels):
            if cid == -1:
                continue
            centroids[cid] = coords_2d[labels == cid].mean(axis=0)

        if centroids:
            centroid_matrix = np.array([centroids[c] for c in sorted(centroids)])
            centroid_ids = sorted(centroids.keys())
            noise_mask = labels == -1
            dists = pairwise_distances(coords_2d[noise_mask], centroid_matrix)
            nearest = dists.argmin(axis=1)
            for j, idx in enumerate(np.where(noise_mask)[0]):
                labels[idx] = centroid_ids[nearest[j]]

    return coords_2d, matrix, labels.tolist()


def generate_archetype_names(
    cluster_id: int,
    member_scores: list[dict],
    dim_set: dict,
    client: OpenAI,
) -> dict:
    """Generate an archetype name and description for a cluster based on its scores."""
    avg_scores = {
        "E_I": np.mean([s["E_I"] for s in member_scores]),
        "S_N": np.mean([s["S_N"] for s in member_scores]),
        "T_F": np.mean([s["T_F"] for s in member_scores]),
        "J_P": np.mean([s["J_P"] for s in member_scores]),
    }

    dims = dim_set["dimensions"]
    score_desc = []
    for key in ["E_I", "S_N", "T_F", "J_P"]:
        d = dims[key]
        first, second = key.split("_")
        val = avg_scores[key]
        pole = d[f"{first}_label"] if val > 0 else d[f"{second}_label"]
        score_desc.append(f"  {d['name']}: {val:+.2f} → {pole}")

    countries = [s["country_id"].replace("_", " ") for s in member_scores]

    prompt = f"""Based on these constitutional personality scores (lens: "{dim_set['name']}"), name this archetype.

## Cluster {cluster_id} — {len(member_scores)} countries
Countries: {', '.join(countries)}

Average dimension scores:
{chr(10).join(score_desc)}

Dominant MBTI letters from averages: {'E' if avg_scores['E_I'] > 0 else 'I'}{'S' if avg_scores['S_N'] > 0 else 'N'}{'T' if avg_scores['T_F'] > 0 else 'F'}{'J' if avg_scores['J_P'] > 0 else 'P'}

Give this cluster:
1. An evocative 2-4 word archetype name
2. A 2-3 sentence description
3. 3-5 key themes

Respond in JSON:
```json
{{"name": "...", "description": "...", "key_themes": ["...", "..."]}}
```"""

    resp = client.chat.completions.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    text = resp.choices[0].message.content
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        result = json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        result = {"name": f"Cluster {cluster_id}", "description": "", "key_themes": []}

    mbti = (
        ("E" if avg_scores["E_I"] > 0 else "I")
        + ("S" if avg_scores["S_N"] > 0 else "N")
        + ("T" if avg_scores["T_F"] > 0 else "F")
        + ("J" if avg_scores["J_P"] > 0 else "P")
    )
    result["mbti"] = mbti
    result["avg_scores"] = {k: round(v, 3) for k, v in avg_scores.items()}
    return result


def process_lens(
    dim_set_id: str,
    dim_set: dict,
    countries: list[dict],
    topic_texts: dict,
    client: OpenAI,
) -> dict:
    """Full pipeline for one lens: score → cluster → name archetypes."""
    print(f"\n  Scoring {len(countries)} constitutions...")
    scores = score_all_constitutions(countries, topic_texts, dim_set, client)

    # Align scores with countries (handle any ordering issues)
    score_lookup = {s["country_id"]: s for s in scores}
    aligned_scores = []
    for c in countries:
        s = score_lookup.get(c["country_id"], {
            "country_id": c["country_id"],
            "E_I": 0.0, "S_N": 0.0, "T_F": 0.0, "J_P": 0.0, "mbti": "????",
        })
        aligned_scores.append(s)

    print(f"  Clustering...")
    coords_2d, matrix, labels = cluster_scores(aligned_scores)

    n_clusters = len(set(labels))
    print(f"  Found {n_clusters} clusters")

    # Group by cluster
    cluster_members: dict[int, list[dict]] = {}
    for i, s in enumerate(aligned_scores):
        cid = labels[i]
        cluster_members.setdefault(cid, []).append(s)

    # Generate archetype names
    print(f"  Naming archetypes...")
    archetypes = {}
    for cid in sorted(cluster_members.keys()):
        members = cluster_members[cid]
        arch = generate_archetype_names(cid, members, dim_set, client)
        arch["cluster_id"] = cid
        arch["countries"] = [s["country_id"] for s in members]
        archetypes[cid] = arch
        print(f"    Cluster {cid}: {arch['name']} ({arch['mbti']}) — {len(members)} countries")

    # Build country assignments
    country_assignments = []
    for i, c in enumerate(countries):
        s = aligned_scores[i]
        cluster_id = labels[i]
        arch = archetypes.get(cluster_id, {})
        country_assignments.append({
            "country_id": c["country_id"],
            "cluster": cluster_id,
            "archetype_name": arch.get("name", "Unknown"),
            "mbti": s.get("mbti", "????"),
            "scores": {
                "E_I": s.get("E_I", 0),
                "S_N": s.get("S_N", 0),
                "T_F": s.get("T_F", 0),
                "J_P": s.get("J_P", 0),
            },
            "umap_x": float(coords_2d[i, 0]),
            "umap_y": float(coords_2d[i, 1]),
        })

    return {
        "dimension_set": dim_set,
        "archetypes": {str(k): v for k, v in archetypes.items()},
        "country_assignments": country_assignments,
    }


def main() -> None:
    out_dir = Path(DATA_RESULTS)
    out_dir.mkdir(parents=True, exist_ok=True)

    countries, topic_texts = load_topic_texts()
    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)

    all_results: dict[str, dict] = {}

    for dim_set_id, dim_set in DIMENSION_SETS.items():
        print(f"\n{'=' * 60}")
        print(f"Processing lens: {dim_set['name']}")
        print(f"{'=' * 60}")

        result = process_lens(dim_set_id, dim_set, countries, topic_texts, client)
        all_results[dim_set_id] = result

    # Save
    out_path = out_dir / "archetypes.json"
    out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
    print(f"\nSaved all results to {out_path}")

    # Summary
    for dim_set_id, result in all_results.items():
        print(f"\n=== {result['dimension_set']['name']} ===")
        for cid in sorted(result["archetypes"].keys(), key=int):
            a = result["archetypes"][cid]
            print(f"  Cluster {cid}: {a['name']} ({a.get('mbti', '?')}) — {len(a['countries'])} countries")

        # Show specific countries
        for name in ["Czech_Republic_the", "United_States_of_America", "Japan", "France"]:
            ca = next((c for c in result["country_assignments"] if c["country_id"] == name), None)
            if ca:
                print(f"    {name}: {ca['mbti']} (scores: {ca['scores']})")


if __name__ == "__main__":
    main()
