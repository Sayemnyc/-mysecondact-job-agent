# My Second Act Job Agent

## Import jobs from pasted text (V2)

1. Paste raw job text into `data/raw_jobs.txt`.
2. Run:

```bash
python -m src.cli import-text
```

The command will:
- Parse pasted job text into structured job records.
- Append valid jobs to `data/jobs.csv`.
- Skip duplicates using `title + company + job_url`.
- Write review items to `output/import_review.md`.

## Daily flow

```bash
python -m src.cli daily
```
