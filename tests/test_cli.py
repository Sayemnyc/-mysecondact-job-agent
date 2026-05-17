from pathlib import Path

from src.cli import main


def test_daily_flow(tmp_path, monkeypatch):
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text(
        "id,title,company,location,description,salary,apply_url\n"
        "1,Senior Python Engineer,Acme,Remote US,Python backend role,150000,https://example.com\n",
        encoding="utf-8",
    )

    report_path = tmp_path / "daily_report.md"
    out_dir = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["cli", "--csv", str(csv_path), "daily", "--out-dir", str(out_dir), "--report", str(report_path)],
    )

    rc = main()
    assert rc == 0
    assert report_path.exists()
    assert any(out_dir.glob("job_*_package.txt"))


def test_import_validation_error(tmp_path, monkeypatch):
    csv_path = tmp_path / "jobs.csv"
    csv_path.write_text("id,title\n1,Only title\n", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["cli", "--csv", str(csv_path), "import-csv"])
    rc = main()
    assert rc == 2
