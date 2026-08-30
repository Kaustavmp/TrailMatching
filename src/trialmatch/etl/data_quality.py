"""
Lightweight data quality checks, run after ETL and before loading into
Postgres. Deliberately dependency-free (no Great Expectations) so it's
easy to read end to end in a code review -- but structured the same way
a GE suite would be: one function per expectation, all results collected
into a single report.
"""
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"


@dataclass
class QualityReport:
    checks: list = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: str = ""):
        self.checks.append({"check": name, "passed": passed, "detail": detail})

    def failed(self) -> list:
        return [c for c in self.checks if not c["passed"]]

    def summary(self) -> str:
        total = len(self.checks)
        passed = total - len(self.failed())
        return f"{passed}/{total} checks passed"


def check_patients(df: pd.DataFrame, report: QualityReport):
    report.add("patients_not_empty", len(df) > 0, f"{len(df)} rows")
    report.add("patient_id_unique", df["patient_id"].is_unique, "duplicate patient_id found" if not df["patient_id"].is_unique else "")
    report.add("gender_no_nulls", df["gender"].notna().all(), f"{df['gender'].isna().sum()} nulls")
    if "birthdate" in df:
        valid_dates = pd.to_datetime(df["birthdate"], errors="coerce").notna()
        report.add("birthdate_parseable", valid_dates.all(), f"{(~valid_dates).sum()} unparseable")


def check_trial_criteria(df: pd.DataFrame, report: QualityReport):
    report.add("trials_not_empty", len(df) > 0, f"{len(df)} rows")
    report.add("nct_id_unique", df["nct_id"].is_unique, "duplicate nct_id found" if not df["nct_id"].is_unique else "")
    sane_ages = df.apply(
        lambda r: r["min_age"] is None or r["max_age"] is None or r["min_age"] <= r["max_age"],
        axis=1,
    )
    report.add("age_range_sane", sane_ages.all(), f"{(~sane_ages).sum()} rows with min_age > max_age")


def main():
    report = QualityReport()

    patients_path = PROCESSED_DIR / "patients.parquet"
    criteria_path = PROCESSED_DIR / "trial_criteria.parquet"

    if patients_path.exists():
        check_patients(pd.read_parquet(patients_path), report)
    else:
        report.add("patients_file_exists", False, str(patients_path))

    if criteria_path.exists():
        check_trial_criteria(pd.read_parquet(criteria_path), report)
    else:
        report.add("criteria_file_exists", False, str(criteria_path))

    print(report.summary())
    for c in report.failed():
        print(f"  FAILED: {c['check']} -- {c['detail']}")

    if report.failed():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
