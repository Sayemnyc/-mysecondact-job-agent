from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

FIELDS = [
    "title",
    "company",
    "location",
    "remote_status",
    "salary",
    "job_url",
    "source",
    "description",
    "date_found",
    "status",
]
REQUIRED_FIELDS = ["title", "company"]


@dataclass
class ImportResult:
    imported: list[dict]
    duplicates: list[dict]
    review: list[dict]


def _split_blocks(raw_text: str) -> list[str]:
    blocks = [b.strip() for b in re.split(r"\n\s*\n+", raw_text) if b.strip()]
    if len(blocks) == 1:
        # Fallback: split when lines look like numbered search results.
        blocks = [b.strip() for b in re.split(r"\n(?=\d+[\.)]\s)", raw_text) if b.strip()]
    return blocks


def _field(patterns: Iterable[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            if match.lastindex:
                return match.group(1).strip()
            return match.group(0).strip()
    return ""


def parse_raw_job_text(raw_text: str) -> list[dict]:
    jobs: list[dict] = []
    for block in _split_blocks(raw_text):
        lines = [ln.strip(" -\t") for ln in block.splitlines() if ln.strip()]
        title = _field([r"(?:^|\n)title\s*:\s*(.+)"], block)
        if not title and lines:
            first = lines[0]
            if not re.match(r"^(company|location|salary|source|description|apply)\s*:", first, flags=re.IGNORECASE):
                title = re.sub(r"\s+[\-–|]\s+.+$", "", first).strip()
        company = _field([r"(?:^|\n)company\s*:\s*(.+)", r"(?:^|\n)at\s+([^\n,|]+)"], block)
        location = _field([r"(?:^|\n)location\s*:\s*(.+)", r"(?:^|\n)([A-Za-z .]+,\s*[A-Z]{2})"], block)
        remote_status = _field([r"(?:^|\n)remote(?:\s*status)?\s*:\s*(.+)"], block)
        if not remote_status:
            if re.search(r"\bremote\b", block, flags=re.IGNORECASE):
                remote_status = "Remote"
            elif re.search(r"\bhybrid\b", block, flags=re.IGNORECASE):
                remote_status = "Hybrid"
            elif re.search(r"\bonsite\b|on-site", block, flags=re.IGNORECASE):
                remote_status = "On-site"
        salary = _field([r"(?:^|\n)salary\s*:\s*(.+)", r"(\$[\d,]+(?:\s*[-–]\s*\$?[\d,]+)?)"], block)
        job_url = _field([r"https?://\S+"], block).rstrip('.,)')
        source = _field([r"(?:^|\n)source\s*:\s*(.+)"], block) or "pasted_text"
        description = _field([r"(?:^|\n)description\s*:\s*([\s\S]+)$"], block)
        if not description:
            description = " ".join(lines[:4])[:500]

        jobs.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "remote_status": remote_status,
                "salary": salary,
                "job_url": job_url,
                "source": source,
                "description": description,
                "date_found": str(date.today()),
                "status": "new",
            }
        )
    return jobs


def _read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _append_csv_rows(path: Path, rows: list[dict]) -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists or path.stat().st_size == 0:
            writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def import_jobs_from_text(raw_text_path: Path, csv_path: Path, review_path: Path) -> ImportResult:
    raw_text = raw_text_path.read_text(encoding="utf-8") if raw_text_path.exists() else ""
    parsed = parse_raw_job_text(raw_text)

    existing = _read_csv_rows(csv_path)
    seen = {(r.get("title", "").strip().lower(), r.get("company", "").strip().lower(), r.get("job_url", "").strip().lower()) for r in existing}

    imported, duplicates, review = [], [], []

    for job in parsed:
        missing = [k for k in REQUIRED_FIELDS if not job.get(k, "").strip()]
        key = (job["title"].strip().lower(), job["company"].strip().lower(), job["job_url"].strip().lower())
        if missing:
            review.append({"job": job, "missing": missing})
            continue
        if key in seen:
            duplicates.append(job)
            continue
        seen.add(key)
        imported.append(job)

    if imported:
        _append_csv_rows(csv_path, imported)

    _write_review(review_path, imported, duplicates, review)
    return ImportResult(imported=imported, duplicates=duplicates, review=review)


def _write_review(path: Path, imported: list[dict], duplicates: list[dict], review: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Import Review", "", "## Successfully Imported"]
    lines.extend([f"- {j['title']} @ {j['company']}" for j in imported] or ["- None"])
    lines += ["", "## Skipped as Duplicates"]
    lines.extend([f"- {j['title']} @ {j['company']}" for j in duplicates] or ["- None"])
    lines += ["", "## Needs Manual Review"]
    if review:
        for item in review:
            j = item["job"]
            lines.append(f"- {j.get('title') or 'Unknown title'} @ {j.get('company') or 'Unknown company'}")
            lines.append(f"  - Missing fields: {', '.join(item['missing'])}")
    else:
        lines.append("- None")

    lines += [
        "",
        "## Suggested Cleanup Instructions",
        "- Add missing title/company lines in `data/raw_jobs.txt` using `Title:` and `Company:` labels.",
        "- Keep one job per paragraph block separated by a blank line.",
        "- Include `Location:`, `Salary:`, and `https://...` when available.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
