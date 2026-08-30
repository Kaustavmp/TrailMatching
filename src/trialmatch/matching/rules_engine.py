"""
Hard eligibility filters. Every trial a patient is shown must pass these --
they are non-negotiable clinical/administrative constraints (age, sex,
required/excluded conditions), as opposed to the embedding-based ranking
below, which is a *soft* preference signal among already-eligible trials.

Kept dependency-free and pure-function so it's trivially unit-testable
(see tests/test_rules_engine.py).
"""
from dataclasses import dataclass
from datetime import date


@dataclass
class FilterResult:
    eligible: bool
    reasons: list[str]


def _age(birthdate: str) -> int | None:
    if not birthdate:
        return None
    try:
        year = int(str(birthdate)[:4])
        return date.today().year - year
    except ValueError:
        return None


def _has_any(patient_conditions: list[str], targets: list[str]) -> bool:
    patient_lower = {c.lower() for c in patient_conditions}
    return any(any(t.lower() in c for c in patient_lower) for t in targets)


def apply_hard_filters(patient: dict, trial_criteria: dict) -> FilterResult:
    reasons = []
    patient_age = _age(patient.get("birthdate"))

    min_age = trial_criteria.get("min_age")
    max_age = trial_criteria.get("max_age")
    if patient_age is not None:
        if min_age is not None and patient_age < min_age:
            reasons.append(f"Patient age {patient_age} is below trial minimum {min_age}")
        if max_age is not None and patient_age > max_age:
            reasons.append(f"Patient age {patient_age} is above trial maximum {max_age}")

    sex = trial_criteria.get("sex")
    if sex and sex.upper() not in ("ALL", "ANY") and patient.get("gender", "").upper() != sex.upper():
        reasons.append(f"Trial requires sex={sex}, patient is {patient.get('gender')}")

    required = trial_criteria.get("required_conditions") or []
    if required and not _has_any(patient.get("conditions", []), required):
        reasons.append("Patient does not have any of the required conditions")

    excluded = trial_criteria.get("excluded_conditions") or []
    if excluded and _has_any(patient.get("conditions", []), excluded):
        reasons.append("Patient has a condition on the trial's exclusion list")

    return FilterResult(eligible=len(reasons) == 0, reasons=reasons)
