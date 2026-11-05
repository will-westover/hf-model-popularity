"""Look up the arXiv papers linked from the collected models.

Run from the repository root after collect_models.py:
    uv run python scripts/collect_arxiv.py

Reads the arXiv IDs out of data/raw/models_raw.csv, asks the arXiv API for
them 100 at a time, and saves one row per paper to data/raw/arxiv_raw.csv.
arXiv asks for about 3 seconds between requests, so this takes a minute or two.
"""
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests

URL = "https://export.arxiv.org/api/query"
BATCH_SIZE = 100
DELAY_SECONDS = 3.0
USER_AGENT = "STAT386-student-project/1.0 (https://github.com/will-westover/hf-model-popularity)"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def parse(xml_text):
    """Pull id, title, published date, and primary category out of one Atom response."""
    rows = []
    for entry in ET.fromstring(xml_text).findall("atom:entry", NS):
        link = entry.find("atom:id", NS).text  # like http://arxiv.org/abs/1908.10084v1
        category = entry.find("atom:category", NS)
        rows.append({
            "arxiv_id": link.split("/abs/")[-1],
            "title": entry.find("atom:title", NS).text,
            "published": entry.find("atom:published", NS).text,
            "primary_category": category.get("term") if category is not None else None,
        })
    return rows


def main():
    models = pd.read_csv("data/raw/models_raw.csv")
    ids = models["arxiv_ids"].dropna().str.split(";").explode().unique()
    print("Looking up", len(ids), "papers")

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    rows = []
    for start in range(0, len(ids), BATCH_SIZE):
        batch = ids[start:start + BATCH_SIZE]
        response = session.get(URL, params={"id_list": ",".join(batch), "max_results": BATCH_SIZE}, timeout=60)
        response.raise_for_status()
        rows += parse(response.text)
        print("  ", len(rows), "papers so far")
        time.sleep(DELAY_SECONDS)

    Path("data/raw").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv("data/raw/arxiv_raw.csv", index=False)
    print("Saved", len(rows), "papers to data/raw/arxiv_raw.csv")


if __name__ == "__main__":
    main()
