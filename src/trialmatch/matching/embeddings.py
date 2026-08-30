"""
Rank hard-eligible trials by semantic similarity between a patient
summary and each trial's description. This is the "soft" layer on top
of matching/rules_engine.py's hard filters -- it never overrides a
hard exclusion, it only orders what's already eligible.
"""
from pathlib import Path

import numpy as np
import pandas as pd

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def patient_summary(patient: dict) -> str:
    conditions = ", ".join(patient.get("conditions", [])) or "no recorded conditions"
    return f"{patient.get('gender', 'unknown')} patient with {conditions}."


def trial_summary(trial: dict) -> str:
    conditions = ", ".join(trial.get("conditions", [])) or "unspecified condition"
    return f"{trial.get('brief_title', '')} — studies {conditions}."


def rank_trials(patient: dict, eligible_trials: list[dict]) -> list[dict]:
    """Return eligible_trials sorted by descending semantic similarity, each
    annotated with a similarity_score field."""
    if not eligible_trials:
        return []

    model = _get_model()
    p_emb = model.encode([patient_summary(patient)])[0]
    t_texts = [trial_summary(t) for t in eligible_trials]
    t_embs = model.encode(t_texts)

    def cosine(a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

    scored = []
    for trial, emb in zip(eligible_trials, t_embs):
        scored.append({**trial, "similarity_score": round(cosine(p_emb, emb), 4)})

    return sorted(scored, key=lambda t: t["similarity_score"], reverse=True)
