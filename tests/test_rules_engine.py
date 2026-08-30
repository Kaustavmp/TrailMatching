import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trialmatch.matching.rules_engine import apply_hard_filters


def make_patient(**overrides):
    base = {
        "patient_id": "p1",
        "gender": "female",
        "birthdate": "1980-01-01",
        "conditions": ["Type 2 diabetes mellitus"],
    }
    base.update(overrides)
    return base


def make_criteria(**overrides):
    base = {
        "min_age": 18,
        "max_age": 75,
        "sex": "ALL",
        "required_conditions": ["diabetes"],
        "excluded_conditions": [],
    }
    base.update(overrides)
    return base


def test_eligible_patient_passes():
    result = apply_hard_filters(make_patient(), make_criteria())
    assert result.eligible
    assert result.reasons == []


def test_age_below_minimum_fails():
    patient = make_patient(birthdate="2015-01-01")  # ~11 years old
    result = apply_hard_filters(patient, make_criteria())
    assert not result.eligible
    assert any("below trial minimum" in r for r in result.reasons)


def test_missing_required_condition_fails():
    patient = make_patient(conditions=["Asthma"])
    result = apply_hard_filters(patient, make_criteria())
    assert not result.eligible
    assert any("required conditions" in r for r in result.reasons)


def test_excluded_condition_fails():
    patient = make_patient(conditions=["Type 2 diabetes mellitus", "Pancreatitis"])
    criteria = make_criteria(excluded_conditions=["pancreatitis"])
    result = apply_hard_filters(patient, criteria)
    assert not result.eligible
    assert any("exclusion list" in r for r in result.reasons)


def test_sex_mismatch_fails():
    patient = make_patient(gender="male")
    criteria = make_criteria(sex="FEMALE")
    result = apply_hard_filters(patient, criteria)
    assert not result.eligible
