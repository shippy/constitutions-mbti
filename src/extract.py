"""Extract structured features from raw constitution data."""

import json
from pathlib import Path

from src.config import DATA_RAW, DATA_PROCESSED


def load_raw_constitutions() -> list[dict]:
    """Load all raw constitution JSONs."""
    raw_dir = Path(DATA_RAW)
    constitutions = []
    for f in sorted(raw_dir.glob("*.json")):
        constitutions.append(json.loads(f.read_text()))
    return constitutions


def build_topic_universe(constitutions: list[dict]) -> list[str]:
    """Get sorted list of all unique topic keys across all constitutions."""
    all_keys: set[str] = set()
    for c in constitutions:
        all_keys.update(c["topics"].keys())
    return sorted(all_keys)


def extract_features(constitutions: list[dict]) -> dict:
    """Build feature matrices from constitutions.

    Returns dict with:
      - countries: list of country metadata dicts
      - topic_keys: sorted list of all topic keys
      - binary_matrix: list of lists (country x topic) with 0/1
      - topic_texts: dict of country_id -> {topic_key: text}
    """
    topic_keys = build_topic_universe(constitutions)
    key_to_idx = {k: i for i, k in enumerate(topic_keys)}

    countries = []
    binary_matrix = []
    topic_texts = {}

    for c in constitutions:
        countries.append({
            "country": c["country"],
            "country_id": c["country_id"],
            "constitution_id": c["constitution_id"],
            "region": c.get("region", ""),
            "year_enacted": c.get("year_enacted", ""),
            "year_revised": c.get("year_revised"),
            "num_topics": len(c["topics"]),
        })

        # Binary presence vector
        row = [0] * len(topic_keys)
        for key in c["topics"]:
            if key in key_to_idx:
                row[key_to_idx[key]] = 1
        binary_matrix.append(row)

        # Topic texts for embedding
        texts = {}
        for key, val in c["topics"].items():
            text = val["text"] if isinstance(val, dict) else val
            if text.strip():
                texts[key] = text
        topic_texts[c["country_id"]] = texts

    return {
        "countries": countries,
        "topic_keys": topic_keys,
        "binary_matrix": binary_matrix,
        "topic_texts": topic_texts,
    }


def main() -> None:
    out_dir = Path(DATA_PROCESSED)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading raw constitutions...")
    constitutions = load_raw_constitutions()
    print(f"Loaded {len(constitutions)} constitutions")

    print("Extracting features...")
    features = extract_features(constitutions)

    print(f"Topic universe: {len(features['topic_keys'])} unique topics")
    topic_counts = [sum(row) for row in features["binary_matrix"]]
    print(f"Topics per country: min={min(topic_counts)}, max={max(topic_counts)}, "
          f"mean={sum(topic_counts)/len(topic_counts):.0f}")

    out_path = out_dir / "features.json"
    out_path.write_text(json.dumps(features, indent=2, ensure_ascii=False))
    print(f"Saved features to {out_path}")


if __name__ == "__main__":
    main()
