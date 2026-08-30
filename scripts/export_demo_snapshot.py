"""
Export a small, precomputed snapshot of patients/trials/matches from
Postgres into flat CSVs for the Hugging Face Space demo.

The Space intentionally does NOT run Prefect/Postgres/dbt live -- free
Spaces have limited, ephemeral compute, so shipping a static snapshot
keeps the demo instant, free to host, and decoupled from this repo's
infrastructure. Re-run this after any full pipeline run to refresh
the demo's data.
"""
import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trialmatch:changeme@localhost:5432/trialmatch")


def export(out_dir: Path, limit_patients: int = 25):
    engine = create_engine(DATABASE_URL)

    patients = pd.read_sql(
        f"SELECT * FROM patients LIMIT {limit_patients}", engine
    )
    matches = pd.read_sql(
        """
        SELECT m.* FROM matches m
        JOIN patients p ON p.patient_id = m.patient_id
        WHERE m.patient_id IN (SELECT patient_id FROM patients LIMIT %(limit)s)
        """,
        engine, params={"limit": limit_patients},
    )
    trials = pd.read_sql(
        "SELECT * FROM trials WHERE nct_id IN (SELECT DISTINCT nct_id FROM matches)", engine
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    patients.to_csv(out_dir / "demo_patients.csv", index=False)
    trials.to_csv(out_dir / "demo_trials.csv", index=False)
    matches.to_csv(out_dir / "demo_matches.csv", index=False)
    print(f"Exported demo snapshot ({len(patients)} patients, {len(trials)} trials, {len(matches)} matches) to {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output directory, e.g. ../huggingface-space/data")
    parser.add_argument("--limit-patients", type=int, default=25)
    args = parser.parse_args()
    export(Path(args.out), args.limit_patients)
