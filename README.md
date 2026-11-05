# What makes a Hugging Face model popular?

STAT 386 data curation project. I pulled the 3,000 most downloaded models on the
[Hugging Face Hub](https://huggingface.co/models) through the public Hub API, then
looked up the arXiv papers each model links to through the arXiv API. The question
is whether a model's task, library, license, or size has anything to do with how
many downloads and likes it gets.

Blog post: <https://will-westover.github.io/blog/posts/hf-model-popularity/>

## Dataset

`data/processed/models_clean.csv` has one row per model (3,000 rows, 28 columns).
Collected November 4, 2026.

| Column | What it is |
| --- | --- |
| `model_id`, `author` | Hub id like `Qwen/Qwen3.8-27B` and the user or org that owns it |
| `task` | Pipeline tag like `text-generation` (missing for 391 models) |
| `library` | Library the model runs with, like `transformers` (missing for 367) |
| `license` | First license tag, like `apache-2.0` (missing for 304) |
| `gated` | True if you have to accept terms before downloading |
| `downloads_30d`, `downloads_all_time` | Download counts from the Hub |
| `likes` | Likes on the Hub |
| `likes_per_million_downloads` | `likes / downloads_all_time * 1e6` |
| `num_parameters`, `params_billions`, `size_class` | Parameter count from safetensors metadata (missing for 1,168 models that don't use safetensors) and a bucket: under 100M, 100M to 1B, 1B to 10B, over 10B |
| `created_at`, `created_at_known`, `created_year`, `age_days` | Creation date. 329 models show the Hub migration date (2022-03-02), so their date is blanked and `created_at_known` is False |
| `last_modified`, `days_since_update` | Last commit to the repo |
| `primary_language`, `num_languages` | From the model card |
| `base_model` | Model this one was fine-tuned or quantized from, if listed |
| `num_datasets`, `num_tags` | Counts of `dataset:` tags and all tags |
| `num_arxiv_papers`, `first_paper_date`, `paper_category`, `days_paper_to_model` | From the arXiv API. Earliest linked paper's date and primary category, and days from that paper to the model's creation |

Raw files in `data/raw/` are untouched API output: `models_raw.json` (full responses),
`models_raw.csv` (one flattened row per model), and `arxiv_raw.csv` (one row per paper).

## Repo contents

```text
hf-model-popularity/
├── README.md
├── pyproject.toml, uv.lock
├── eda.qmd, eda.html          exploratory analysis
├── scripts/
│   ├── collect_models.py      Hub API -> data/raw/models_raw.{json,csv}
│   ├── collect_arxiv.py       arXiv API -> data/raw/arxiv_raw.csv
│   └── clean_data.py          raw files -> data/processed/models_clean.csv
└── data/
    ├── raw/
    └── processed/
```

## Reproduce

No API key is needed for either API.

```bash
uv sync
uv run python scripts/collect_models.py   # 3 requests, a few seconds
uv run python scripts/collect_arxiv.py    # 8 requests, 3 s apart
uv run python scripts/clean_data.py
uv run quarto render eda.qmd
```

Downloads and likes change daily, so a fresh run will not match the CSV here exactly.

## Sources and terms

- [Hub API docs](https://huggingface.co/docs/hub/api) and
  [rate limits](https://huggingface.co/docs/hub/rate-limits). The list endpoint is
  public, allows 500 requests per 5 minutes without a token, and
  [robots.txt](https://huggingface.co/robots.txt) allows everything.
- [arXiv API](https://info.arxiv.org/help/api/index.html), which asks for one request
  every 3 seconds. The script waits 3 seconds between batches.
- Model metadata is public, and the dataset holds only metadata (no model weights,
  no user data beyond public org names), so it is included here.
