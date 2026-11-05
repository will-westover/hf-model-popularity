"""Collect the most downloaded models on the Hugging Face Hub.

Run from the repository root:
    uv run python scripts/collect_models.py

Uses the public list endpoint (no API key needed). The expand[] parameter
asks for extra fields so one request per page is enough. Saves the raw API
responses to data/raw/models_raw.json and one flattened row per model to
data/raw/models_raw.csv. Cleaning happens later in scripts/clean_data.py.
"""
import json
import time
from pathlib import Path

import pandas as pd
import requests

N_MODELS = 3000
PAGE_SIZE = 1000
URL = "https://huggingface.co/api/models"
EXPAND = [
    "author", "pipeline_tag", "library_name", "tags", "cardData", "downloads",
    "downloadsAllTime", "likes", "createdAt", "lastModified", "safetensors", "gated",
]
USER_AGENT = "STAT386-student-project/1.0 (https://github.com/will-westover/hf-model-popularity)"
DELAY_SECONDS = 1.0


def join(value):
    """Turn a list from cardData into one string, leave strings and None alone."""
    if isinstance(value, list):
        return ";".join(str(v) for v in value)
    return value


def flatten(model):
    """Pick the fields we want out of one API record."""
    tags = model.get("tags", [])
    card = model.get("cardData") or {}
    safetensors = model.get("safetensors") or {}
    return {
        "model_id": model["id"],
        "author": model.get("author"),
        "task": model.get("pipeline_tag"),
        "library": model.get("library_name"),
        "license": ";".join(t[len("license:"):] for t in tags if t.startswith("license:")),
        "downloads_30d": model.get("downloads"),
        "downloads_all_time": model.get("downloadsAllTime"),
        "likes": model.get("likes"),
        "created_at": model.get("createdAt"),
        "last_modified": model.get("lastModified"),
        "gated": model.get("gated"),
        "num_parameters": safetensors.get("total"),
        "language": join(card.get("language")),
        "base_model": join(card.get("base_model")),
        "arxiv_ids": ";".join(t[len("arxiv:"):] for t in tags if t.startswith("arxiv:")),
        "num_datasets": sum(t.startswith("dataset:") for t in tags),
        "num_tags": len(tags),
    }


def main():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    params = {"sort": "downloads", "direction": -1, "limit": PAGE_SIZE, "expand[]": EXPAND}
    url = URL
    pages = []
    while url and sum(len(p) for p in pages) < N_MODELS:
        print("Fetching", url[:80], "...")
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
        pages.append(response.json())
        print("  got", len(pages[-1]), "models; rate limit left:", response.headers.get("ratelimit"))
        url = response.links.get("next", {}).get("url")
        params = None  # the next link already carries the query string
        time.sleep(DELAY_SECONDS)

    models = [m for page in pages for m in page][:N_MODELS]

    Path("data/raw").mkdir(parents=True, exist_ok=True)
    with open("data/raw/models_raw.json", "w") as f:
        json.dump(models, f)
    pd.DataFrame([flatten(m) for m in models]).to_csv("data/raw/models_raw.csv", index=False)
    print("Saved", len(models), "models to data/raw/models_raw.csv")


if __name__ == "__main__":
    main()
