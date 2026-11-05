"""Build the processed dataset from the two raw files.

Run from the repository root after both collect scripts:
    uv run python scripts/clean_data.py

Reads data/raw/models_raw.csv and data/raw/arxiv_raw.csv and writes
data/processed/models_clean.csv with one row per model. The raw files
are never changed.
"""
from pathlib import Path

import pandas as pd

COLLECTED_ON = pd.Timestamp("2026-11-04", tz="UTC")
PLACEHOLDER_DATE = "2022-03-02"  # the Hub migration date, not a real creation date

models = pd.read_csv("data/raw/models_raw.csv")
papers = pd.read_csv("data/raw/arxiv_raw.csv")

# One paper can be linked by many models, so summarize papers per model.
papers["arxiv_id"] = papers["arxiv_id"].str.replace(r"v\d+$", "", regex=True)
papers["published"] = pd.to_datetime(papers["published"])
links = models[["model_id", "arxiv_ids"]].dropna()
links = links.assign(arxiv_id=links["arxiv_ids"].str.split(";")).explode("arxiv_id")
links = links.merge(papers, on="arxiv_id", how="left").sort_values("published")
per_model = links.groupby("model_id").agg(
    num_arxiv_papers=("arxiv_id", "size"),
    first_paper_date=("published", "min"),
    paper_category=("primary_category", "first"),
)
models = models.merge(per_model, on="model_id", how="left")
models["num_arxiv_papers"] = models["num_arxiv_papers"].fillna(0).astype(int)

# Dates. Models created exactly on the migration date get their date blanked.
models["created_at"] = pd.to_datetime(models["created_at"])
models["last_modified"] = pd.to_datetime(models["last_modified"])
models["created_at_known"] = models["created_at"].dt.strftime("%Y-%m-%d") != PLACEHOLDER_DATE
models.loc[~models["created_at_known"], "created_at"] = pd.NaT
models["created_year"] = models["created_at"].dt.year
models["age_days"] = (COLLECTED_ON - models["created_at"]).dt.days
models["days_since_update"] = (COLLECTED_ON - models["last_modified"]).dt.days
models["days_paper_to_model"] = (models["created_at"] - models["first_paper_date"]).dt.days

# Categorical cleanup.
models["license"] = models["license"].str.split(";").str[0]
models["gated"] = models["gated"] != "False"
models["primary_language"] = models["language"].str.split(";").str[0]
models["num_languages"] = models["language"].str.split(";").str.len()

# Size in billions of parameters plus a bucket for grouping.
models["params_billions"] = models["num_parameters"] / 1e9
models["size_class"] = pd.cut(
    models["params_billions"],
    bins=[0, 0.1, 1, 10, float("inf")],
    labels=["under 100M", "100M to 1B", "1B to 10B", "over 10B"],
)

# Likes relative to use.
models["likes_per_million_downloads"] = models["likes"] / models["downloads_all_time"] * 1e6

columns = [
    "model_id", "author", "task", "library", "license", "gated",
    "downloads_30d", "downloads_all_time", "likes", "likes_per_million_downloads",
    "num_parameters", "params_billions", "size_class",
    "created_at", "created_at_known", "created_year", "age_days",
    "last_modified", "days_since_update",
    "primary_language", "num_languages", "base_model", "num_datasets", "num_tags",
    "num_arxiv_papers", "first_paper_date", "paper_category", "days_paper_to_model",
]
models = models[columns]

Path("data/processed").mkdir(parents=True, exist_ok=True)
models.to_csv("data/processed/models_clean.csv", index=False)
print("Saved", len(models), "rows and", len(columns), "columns to data/processed/models_clean.csv")
print(models.isna().sum())
