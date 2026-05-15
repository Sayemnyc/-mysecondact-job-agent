from __future__ import annotations

import argparse
from pathlib import Path

from src.import_from_text import import_jobs_from_text


def run_import_text() -> int:
    result = import_jobs_from_text(
        raw_text_path=Path("data/raw_jobs.txt"),
        csv_path=Path("data/jobs.csv"),
        review_path=Path("output/import_review.md"),
    )
    print("Import complete!")
    print(f"- Imported: {len(result.imported)}")
    print(f"- Duplicates skipped: {len(result.duplicates)}")
    print(f"- Needs review: {len(result.review)}")
    print("See output/import_review.md for details.")
    return 0


def run_daily() -> int:
    print("Daily flow complete.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Job Agent CLI")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("import-text", help="Import jobs from data/raw_jobs.txt")
    sub.add_parser("daily", help="Run daily flow")

    args = parser.parse_args()

    if args.command == "import-text":
        return run_import_text()
    if args.command == "daily":
        return run_daily()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
