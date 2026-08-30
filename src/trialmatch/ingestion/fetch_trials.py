"""
Ingest clinical trials from the public ClinicalTrials.gov API (v2).

Docs: https://clinicaltrials.gov/data-api/api

Pulls studies matching a condition, paginates through results, and lands
the raw response as Parquet — this is the "bronze" / raw layer of the
pipeline. No transformation happens here on purpose: ingestion should be
dumb and resumable, transformation happens in etl/.
"""
import argparse
import os
import time
from pathlib import Path

import pandas as pd
import requests

CTGOV_API_BASE = os.getenv("CTGOV_API_BASE", "https://clinicaltrials.gov/api/v2/studies")
RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw" / "trials"


def fetch_trials(condition: str, max_studies: int = 200, page_size: int = 100) -> pd.DataFrame:
    """Page through the ClinicalTrials.gov API for a given condition."""
    records = []
    next_page_token = None

    while len(records) < max_studies:
        params = {
            "query.cond": condition,
            "pageSize": min(page_size, max_studies - len(records)),
            "format": "json",
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        resp = requests.get(CTGOV_API_BASE, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        for study in payload.get("studies", []):
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            eligibility = protocol.get("eligibilityModule", {})
            status = protocol.get("statusModule", {})
            conditions_module = protocol.get("conditionsModule", {})

            records.append({
                "nct_id": identification.get("nctId"),
                "brief_title": identification.get("briefTitle"),
                "overall_status": status.get("overallStatus"),
                "conditions": conditions_module.get("conditions", []),
                "eligibility_criteria": eligibility.get("eligibilityCriteria"),
                "min_age_raw": eligibility.get("minimumAge"),
                "max_age_raw": eligibility.get("maximumAge"),
                "sex": eligibility.get("sex"),
                "healthy_volunteers": eligibility.get("healthyVolunteers"),
            })

        next_page_token = payload.get("nextPageToken")
        if not next_page_token:
            break
        time.sleep(0.2)  # be polite to the API

    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser(description="Fetch trials from ClinicalTrials.gov")
    parser.add_argument("--condition", required=True, help='e.g. "breast cancer"')
    parser.add_argument("--max-studies", type=int, default=200)
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df = fetch_trials(args.condition, args.max_studies)

    out_path = RAW_DIR / f"trials_{args.condition.replace(' ', '_')}.parquet"
    df.to_parquet(out_path, index=False)
    print(f"Wrote {len(df)} trials to {out_path}")


if __name__ == "__main__":
    main()
