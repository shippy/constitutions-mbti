"""Collect constitutions from the Constitute Project API."""

import asyncio
import json
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from src.config import DATA_RAW

BASE_URL = "https://www.constituteproject.org/service"


async def fetch_constitution_list(client: httpx.AsyncClient) -> list[dict]:
    """Fetch list of all constitutions, return only current in-force ones."""
    resp = await client.get(f"{BASE_URL}/constitutions", params={"lang": "en"})
    resp.raise_for_status()
    all_cons = resp.json()

    # Keep only in-force, non-draft, public constitutions
    # For countries with multiple entries, keep the most recent
    by_country: dict[str, dict] = {}
    for c in all_cons:
        if not c.get("in_force") or c.get("is_draft") or not c.get("public"):
            continue
        cid = c["country_id"]
        if cid not in by_country or (c.get("year_revised") or c["year_enacted"]) > (
            by_country[cid].get("year_revised") or by_country[cid]["year_enacted"]
        ):
            by_country[cid] = c
    return list(by_country.values())


async def fetch_topics_index(client: httpx.AsyncClient) -> dict[str, str]:
    """Fetch topic key -> label mapping."""
    resp = await client.get(f"{BASE_URL}/topics", params={"lang": "en"})
    resp.raise_for_status()
    topics = resp.json()

    mapping: dict[str, str] = {}

    def walk(items: list[dict]) -> None:
        for t in items:
            mapping[t["key"]] = t["label"]
            if t.get("topics"):
                walk(t["topics"])

    walk(topics)
    return mapping


def parse_html_constitution(html: str, topic_labels: dict[str, str]) -> dict:
    """Parse constitution HTML into plain text and topic-tagged sections."""
    soup = BeautifulSoup(html, "html.parser")

    # Extract full plain text
    full_text = soup.get_text(separator="\n", strip=True)

    # Extract topic-tagged sections
    topics: dict[str, list[str]] = {}
    for el in soup.find_all(attrs={"data-topics": True}):
        raw_topics = el["data-topics"]
        text = el.get_text(separator=" ", strip=True)
        if not text:
            continue

        for topic_ref in raw_topics.split(","):
            # Handle both bare keys and full URIs
            key = topic_ref.strip().split("/")[-1] if "/" in topic_ref else topic_ref.strip()
            if key:
                topics.setdefault(key, [])
                topics[key].append(text)

    # Merge multiple sections per topic into single strings
    merged_topics = {}
    for key, texts in topics.items():
        label = topic_labels.get(key, key)
        merged_topics[key] = {
            "label": label,
            "text": "\n\n".join(texts),
        }

    return {"full_text": full_text, "topics": merged_topics}


async def fetch_one_constitution(
    client: httpx.AsyncClient,
    cons: dict,
    topic_labels: dict[str, str],
    sem: asyncio.Semaphore,
) -> dict:
    """Fetch and parse a single constitution."""
    async with sem:
        resp = await client.get(
            f"{BASE_URL}/html",
            params={"cons_id": cons["id"], "lang": "en"},
        )
        resp.raise_for_status()
        data = resp.json()

    parsed = parse_html_constitution(data.get("html", ""), topic_labels)

    return {
        "country": cons["country"],
        "country_id": cons["country_id"],
        "constitution_id": cons["id"],
        "region": cons.get("region", ""),
        "year_enacted": cons.get("year_enacted", ""),
        "year_revised": cons.get("year_revised"),
        "full_text": parsed["full_text"],
        "topics": parsed["topics"],
    }


async def collect_all() -> None:
    """Main collection pipeline."""
    out_dir = Path(DATA_RAW)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Rate limit: max 5 concurrent requests
    sem = asyncio.Semaphore(5)

    async with httpx.AsyncClient(timeout=30) as client:
        print("Fetching constitution list...")
        constitutions = await fetch_constitution_list(client)
        print(f"Found {len(constitutions)} in-force constitutions")

        print("Fetching topics index...")
        topic_labels = await fetch_topics_index(client)
        print(f"Found {len(topic_labels)} topic keys")

        print("Fetching constitution texts...")
        tasks = [
            fetch_one_constitution(client, c, topic_labels, sem) for c in constitutions
        ]

        results = []
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            result = await coro
            results.append(result)
            if (i + 1) % 20 == 0:
                print(f"  {i + 1}/{len(tasks)} fetched...")

        # Save each constitution
        for r in results:
            filename = re.sub(r"[^a-zA-Z0-9_]", "_", r["country_id"]) + ".json"
            (out_dir / filename).write_text(json.dumps(r, indent=2, ensure_ascii=False))

        print(f"Saved {len(results)} constitutions to {out_dir}/")


if __name__ == "__main__":
    asyncio.run(collect_all())
