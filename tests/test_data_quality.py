import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trialmatch.etl.data_quality import QualityReport, check_patients, check_trial_criteria


def test_check_patients_flags_duplicate_ids():
    df = pd.DataFrame({
        "patient_id": ["p1", "p1"],
        "gender": ["female", "male"],
        "birthdate": ["1980-01-01", "1990-01-01"],
    })
    report = QualityReport()
    check_patients(df, report)
    failed_names = [c["check"] for c in report.failed()]
    assert "patient_id_unique" in failed_names


def test_check_trial_criteria_flags_bad_age_range():
    df = pd.DataFrame({
        "nct_id": ["NCT001"],
        "min_age": [80],
        "max_age": [18],
    })
    report = QualityReport()
    check_trial_criteria(df, report)
    failed_names = [c["check"] for c in report.failed()]
    assert "age_range_sane" in failed_names
