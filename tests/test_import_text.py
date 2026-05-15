from pathlib import Path

from src.import_from_text import import_jobs_from_text


def test_import_text_and_review(tmp_path: Path) -> None:
    raw = tmp_path / "raw_jobs.txt"
    csv_file = tmp_path / "jobs.csv"
    review = tmp_path / "import_review.md"

    raw.write_text(
        """
Title: Software Engineer
Company: Bright Co
Location: Remote
https://example.com/1

Company: No Title Inc
Location: Boston, MA
""".strip()
    )

    result = import_jobs_from_text(raw, csv_file, review)

    assert len(result.imported) == 1
    assert len(result.review) == 1
    text = review.read_text()
    assert "Successfully Imported" in text
    assert "Needs Manual Review" in text
    assert "Missing fields: title" in text


def test_duplicate_prevention(tmp_path: Path) -> None:
    raw = tmp_path / "raw_jobs.txt"
    csv_file = tmp_path / "jobs.csv"
    review = tmp_path / "import_review.md"

    raw.write_text(
        """
Title: DevOps Engineer
Company: Stable Systems
https://example.com/2

Title: DevOps Engineer
Company: Stable Systems
https://example.com/2
""".strip()
    )

    result = import_jobs_from_text(raw, csv_file, review)
    assert len(result.imported) == 1
    assert len(result.duplicates) == 1

    rows = [line for line in csv_file.read_text().splitlines() if line.strip()]
    assert len(rows) == 2  # header + one record
