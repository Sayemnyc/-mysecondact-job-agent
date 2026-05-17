# MySecondAct Job Agent

Simple CLI for daily job intake and application prep.

## Run daily flow

```bash
python -m src.cli daily
```

## Commands

- `python -m src.cli import-csv` — load and validate `data/jobs.csv`
- `python -m src.cli score` — run scam checks and score jobs
- `python -m src.cli generate` — create packages only for `Strong Apply` jobs
- `python -m src.cli report` — generate `output/daily_report.md`
- `python -m src.cli daily` — run full flow (import → scam check → score → generate → report)
