"""
Self-contained copy of the core matching logic (hard filters + a simple
relevance score) so this Space has zero dependency on the GitHub repo's
package layout or a live database. It mirrors
github-repo/src/trialmatch/matching/rules_engine.py exactly -- kept in
sync by hand since the two deploy targets (Space vs. repo) intentionally
don't share a runtime.
"""
from dataclasses import dataclass


@dataclass
class FilterResult:
    eligible: bool
    reasons: list


def _has_any(patient_conditions, targets):
    patient_lower = {c.lower() for c in patient_conditions}
    return any(any(str(t).lower() in c for c in patient_lower) for t in targets)


def apply_hard_filters(patient: dict, trial: dict) -> FilterResult:
    reasons = []
    age = patient.get("age")

    min_age = trial.get("min_age")
    max_age = trial.get("max_age")
    if age is not None:
        if min_age is not None and not pd_isna(min_age) and age < min_age:
            reasons.append(f"Patient age {age} is below trial minimum {int(min_age)}")
        if max_age is not None and not pd_isna(max_age) and age > max_age:
            reasons.append(f"Patient age {age} is above trial maximum {int(max_age)}")

    sex = trial.get("sex")
    if sex and str(sex).upper() not in ("ALL", "ANY") and patient.get("gender", "").upper() != str(sex).upper():
        reasons.append(f"Trial requires sex={sex}, patient is {patient.get('gender')}")

    required = trial.get("required_conditions") or []
    if required and not _has_any(patient.get("conditions", []), required):
        reasons.append("Patient does not have any of the required conditions")

    excluded = trial.get("excluded_conditions") or []
    if excluded and _has_any(patient.get("conditions", []), excluded):
        reasons.append("Patient has a condition on the trial's exclusion list")

    return FilterResult(eligible=len(reasons) == 0, reasons=reasons)


def pd_isna(value) -> bool:
    """Tiny local NaN check so this file has no pandas import requirement."""
    try:
        return value != value  # NaN != NaN is True
    except Exception:
        return False


def relevance_score(patient: dict, trial: dict) -> float:
    """Simple, explainable relevance score (0-1) used for ranking eligible
    trials in the demo: overlap between patient conditions and the
    trial's condition focus, as a stand-in for the full pipeline's
    sentence-transformer embedding similarity (which needs a model
    download not worth carrying in this lightweight demo)."""
    patient_conditions = {c.lower() for c in patient.get("conditions", [])}
    trial_conditions = {c.lower() for c in trial.get("conditions", [])}
    if not patient_conditions or not trial_conditions:
        return 0.5
    overlap = len(patient_conditions & trial_conditions)
    return round(0.5 + 0.5 * (overlap / max(len(trial_conditions), 1)), 3)
