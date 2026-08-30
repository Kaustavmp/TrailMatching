"""
FastAPI serving layer. Reads matches (already computed by the offline
pipeline) out of Postgres/`fct_matches` and exposes them as a clean REST
API -- this is the interface a real front end (or the Streamlit demo)
would call.
"""
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from trialmatch.db.session import get_session

app = FastAPI(
    title="TrialMatch API",
    description="Explainable clinical trial matching for synthetic patients.",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, session: Session = Depends(get_session)):
    row = session.execute(
        text("SELECT * FROM patients WHERE patient_id = :pid"), {"pid": patient_id}
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    return dict(row)


@app.get("/trials/{nct_id}")
def get_trial(nct_id: str, session: Session = Depends(get_session)):
    row = session.execute(
        text("SELECT * FROM trials WHERE nct_id = :nid"), {"nid": nct_id}
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Trial not found")
    return dict(row)


@app.get("/match/{patient_id}")
def get_matches(patient_id: str, limit: int = 10, session: Session = Depends(get_session)):
    """Ranked, explainable trial matches for a patient, eligible-only,
    ordered by similarity_score."""
    rows = session.execute(
        text("""
            SELECT nct_id, eligible, similarity_score, exclusion_reasons
            FROM matches
            WHERE patient_id = :pid AND eligible = true
            ORDER BY similarity_score DESC
            LIMIT :limit
        """),
        {"pid": patient_id, "limit": limit},
    ).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail="No matches found for this patient")

    return {"patient_id": patient_id, "matches": [dict(r) for r in rows]}
