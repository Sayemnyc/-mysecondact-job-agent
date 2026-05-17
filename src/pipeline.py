from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REQUIRED_COLUMNS = ["id", "title", "company", "location", "description", "salary", "apply_url"]


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    description: str
    salary: str
    apply_url: str
    score: int = 0
    label: str = "Needs Review"
    rejection_reason: str = ""
    scam_flags: str = ""

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Job":
        return cls(
            id=row["id"].strip(),
            title=row["title"].strip(),
            company=row["company"].strip(),
            location=row["location"].strip(),
            description=row["description"].strip(),
            salary=row["salary"].strip(),
            apply_url=row["apply_url"].strip(),
            score=int(row.get("score") or 0),
            label=(row.get("label") or "Needs Review").strip(),
            rejection_reason=(row.get("rejection_reason") or "").strip(),
            scam_flags=(row.get("scam_flags") or "").strip(),
        )


def validate_headers(headers: list[str] | None) -> None:
    if not headers:
        raise ValueError("The CSV file is empty. Please add at least one job row.")
    missing = [col for col in REQUIRED_COLUMNS if col not in headers]
    if missing:
        raise ValueError(
            "Your CSV is missing required column(s): "
            + ", ".join(missing)
            + ". Please update data/jobs.csv and try again."
        )


def validate_row(row: dict[str, str], row_num: int) -> None:
    missing_fields = [col for col in REQUIRED_COLUMNS if not (row.get(col) or "").strip()]
    if missing_fields:
        raise ValueError(
            f"Job row {row_num} is missing: {', '.join(missing_fields)}. "
            "Please fill those fields in data/jobs.csv."
        )


def import_csv(csv_path: Path) -> list[Job]:
    if not csv_path.exists():
        raise ValueError(f"Couldn't find {csv_path}. Please create that file first.")

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        validate_headers(reader.fieldnames)
        jobs: list[Job] = []
        for idx, row in enumerate(reader, start=2):
            validate_row(row, idx)
            jobs.append(Job.from_row(row))
    return jobs


def run_scam_check(jobs: Iterable[Job]) -> None:
    for job in jobs:
        flags: list[str] = []
        if "crypto" in job.description.lower() and "unpaid" in job.description.lower():
            flags.append("crypto + unpaid")
        if "wire money" in job.description.lower() or "pay upfront" in job.description.lower():
            flags.append("money transfer request")
        job.scam_flags = "; ".join(flags)


def score_jobs(jobs: Iterable[Job]) -> None:
    for job in jobs:
        score = 50
        desc = job.description.lower()
        if "python" in desc:
            score += 15
        if "remote" in job.location.lower() or "remote" in desc:
            score += 15
        if "senior" in job.title.lower():
            score += 10
        if job.scam_flags:
            score -= 50

        job.score = max(score, 0)
        if job.score >= 70 and not job.scam_flags:
            job.label = "Strong Apply"
            job.rejection_reason = ""
        elif job.score >= 50:
            job.label = "Maybe"
            job.rejection_reason = "Needs manual review"
        else:
            job.label = "Reject"
            job.rejection_reason = "Low match or risk flags"


def generate_packages(jobs: Iterable[Job], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for job in jobs:
        if job.label != "Strong Apply":
            continue
        file_path = out_dir / f"job_{job.id}_package.txt"
        file_path.write_text(
            f"Application package for {job.title} at {job.company}\n"
            f"Location: {job.location}\n"
            f"Apply: {job.apply_url}\n",
            encoding="utf-8",
        )
        generated.append(file_path)
    return generated


def generate_report(jobs: Iterable[Job], report_path: Path) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    jobs_list = list(jobs)
    lines = ["# Daily Job Report", "", f"Total jobs: {len(jobs_list)}", ""]
    for job in jobs_list:
        lines.append(f"- [{job.label}] {job.title} @ {job.company} (score={job.score})")
        if job.rejection_reason:
            lines.append(f"  - reason: {job.rejection_reason}")
        if job.scam_flags:
            lines.append(f"  - scam flags: {job.scam_flags}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
