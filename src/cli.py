from __future__ import annotations

import argparse
from pathlib import Path

from src.pipeline import generate_packages, generate_report, import_csv, run_scam_check, score_jobs


DEFAULT_CSV = Path("data/jobs.csv")
DEFAULT_OUT = Path("output")


def cmd_import_csv(args: argparse.Namespace) -> int:
    jobs = import_csv(Path(args.csv))
    print(f"Imported {len(jobs)} jobs from {args.csv}.")
    return 0


def _load_and_score(csv_path: Path):
    jobs = import_csv(csv_path)
    run_scam_check(jobs)
    score_jobs(jobs)
    return jobs


def cmd_score(args: argparse.Namespace) -> int:
    jobs = _load_and_score(Path(args.csv))
    print(f"Scored {len(jobs)} jobs.")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    jobs = _load_and_score(Path(args.csv))
    generated = generate_packages(jobs, Path(args.out_dir))
    print(f"Generated {len(generated)} package(s) in {args.out_dir}.")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    jobs = _load_and_score(Path(args.csv))
    report = generate_report(jobs, Path(args.report))
    print(f"Report saved to {report}.")
    return 0


def cmd_daily(args: argparse.Namespace) -> int:
    jobs = import_csv(Path(args.csv))
    run_scam_check(jobs)
    score_jobs(jobs)
    generated = generate_packages(jobs, Path(args.out_dir))
    report = generate_report(jobs, Path(args.report))
    print(f"Daily flow complete: jobs={len(jobs)}, packages={len(generated)}, report={report}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Job intake CLI")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Path to jobs CSV (default: data/jobs.csv)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_import = subparsers.add_parser("import-csv", help="Import and validate CSV jobs")
    p_import.set_defaults(func=cmd_import_csv)

    p_score = subparsers.add_parser("score", help="Run scam check and score jobs")
    p_score.set_defaults(func=cmd_score)

    p_generate = subparsers.add_parser("generate", help="Generate packages for Strong Apply jobs")
    p_generate.add_argument("--out-dir", default=str(DEFAULT_OUT), help="Output folder for application packages")
    p_generate.set_defaults(func=cmd_generate)

    p_report = subparsers.add_parser("report", help="Generate markdown report")
    p_report.add_argument("--report", default="output/daily_report.md", help="Report output path")
    p_report.set_defaults(func=cmd_report)

    p_daily = subparsers.add_parser("daily", help="Run import -> scam check -> score -> generate -> report")
    p_daily.add_argument("--out-dir", default=str(DEFAULT_OUT), help="Output folder for application packages")
    p_daily.add_argument("--report", default="output/daily_report.md", help="Report output path")
    p_daily.set_defaults(func=cmd_daily)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
