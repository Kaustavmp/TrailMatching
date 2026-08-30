"""
Combine hard-filter results and the similarity ranking into a single,
auditable explanation object per (patient, trial) pair. This is the
piece that makes TrialMatch a credible healthcare tool rather than a
black box -- every recommendation, and every rejection, is traceable.
"""
from matching.rules_engine import apply_hard_filters


def explain_match(patient: dict, trial: dict, trial_criteria: dict, similarity_score: float | None = None) -> dict:
    filter_result = apply_hard_filters(patient, trial_criteria)

    return {
        "patient_id": patient.get("patient_id"),
        "nct_id": trial.get("nct_id"),
        "eligible": filter_result.eligible,
        "exclusion_reasons": filter_result.reasons,
        "similarity_score": similarity_score,
        "recommendation": (
            "Eligible — ranked by relevance" if filter_result.eligible
            else "Not eligible — see exclusion_reasons"
        ),
    }
