"""Embed constitution topic sections using OpenRouter."""

import json
from pathlib import Path

import numpy as np
from openai import OpenAI
from sklearn.preprocessing import StandardScaler

from src.config import DATA_PROCESSED, EMBEDDING_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL


def get_client() -> OpenAI:
    return OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)


def embed_texts(client: OpenAI, texts: list[str], batch_size: int = 50) -> list[list[float]]:
    """Embed a list of texts in batches."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        # Truncate very long texts to ~8000 chars to stay within token limits
        batch = [t[:8000] for t in batch]
        resp = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        all_embeddings.extend([d.embedding for d in resp.data])
        if (i + batch_size) % 200 == 0:
            print(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)} texts...")
    return all_embeddings


def main() -> None:
    proc_dir = Path(DATA_PROCESSED)
    features_path = proc_dir / "features.json"
    out_path = proc_dir / "embeddings.npz"

    if out_path.exists():
        print(f"Embeddings already cached at {out_path}. Delete to re-compute.")
        return

    print("Loading features...")
    features = json.loads(features_path.read_text())
    countries = features["countries"]
    topic_texts = features["topic_texts"]
    binary_matrix = np.array(features["binary_matrix"], dtype=np.float64)
    topic_keys = features["topic_keys"]

    print(f"Binary features shape: {binary_matrix.shape}")

    # Build per-country text to embed: concatenate all topic texts
    # Then we'll get one embedding per country
    country_texts = []
    for c in countries:
        cid = c["country_id"]
        texts = topic_texts.get(cid, {})
        # Concatenate all topic texts with headers
        parts = []
        for key, text in texts.items():
            parts.append(f"[{key}] {text}")
        combined = "\n\n".join(parts)
        # If too long, truncate
        country_texts.append(combined[:8000] if combined else "No content")

    print(f"Embedding {len(country_texts)} constitutions...")
    client = get_client()
    embeddings = embed_texts(client, country_texts)
    embedding_matrix = np.array(embeddings, dtype=np.float64)
    print(f"Embedding shape: {embedding_matrix.shape}")

    # Normalize both feature sets separately
    print("Normalizing and combining features...")
    scaler_binary = StandardScaler()
    scaler_embed = StandardScaler()

    binary_scaled = scaler_binary.fit_transform(binary_matrix)
    embed_scaled = scaler_embed.fit_transform(embedding_matrix)

    # Concatenate
    combined = np.concatenate([binary_scaled, embed_scaled], axis=1)
    print(f"Combined feature matrix shape: {combined.shape}")

    # Save
    country_ids = [c["country_id"] for c in countries]
    np.savez(
        out_path,
        combined=combined,
        binary=binary_scaled,
        embeddings=embed_scaled,
        country_ids=np.array(country_ids),
        topic_keys=np.array(topic_keys),
    )
    print(f"Saved embeddings to {out_path}")


if __name__ == "__main__":
    main()
