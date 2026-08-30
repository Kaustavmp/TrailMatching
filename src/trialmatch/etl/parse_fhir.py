"""
Flatten raw FHIR patient bundles (from Synthea or the fallback generator)
into a single tabular DataFrame, and persist it as the "silver" layer.

FHIR bundles are deeply nested JSON -- this is the messy, real-world part
of the pipeline that a lot of toy projects skip past.
"""
import json
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw" / "patients"
PROCESSED_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"


def flatten_bundle(bundle: dict) -> dict:
    patient_row = {"patient_id": None, "gender": None, "birthdate": None, "conditions": []}

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        rtype = resource.get("resourceType")

        if rtype == "Patient":
            patient_row["patient_id"] = resource.get("id")
            patient_row["gender"] = resource.get("gender")
            patient_row["birthdate"] = resource.get("birthDate")

        elif rtype == "Condition":
            code = resource.get("code", {})
            text = code.get("text") or (code.get("coding", [{}])[0].get("display"))
            if text:
                patient_row["conditions"].append(text)

        elif rtype == "MedicationRequest":
            patient_row.setdefault("medications", [])
            med = resource.get("medicationCodeableConcept", {}).get("text")
            if med:
                patient_row["medications"].append(med)

    return patient_row


def build_patient_table(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    rows = []
    for path in sorted(raw_dir.glob("*.json")):
        with open(path) as f:
            bundle = json.load(f)
        rows.append(flatten_bundle(bundle))
    return pd.DataFrame(rows)


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = build_patient_table()

    if df.empty:
        print(f"No patient bundles found in {RAW_DIR} -- run ingestion first.")
        return

    out_path = PROCESSED_DIR / "patients.parquet"
    df.to_parquet(out_path, index=False)
    print(f"Flattened {len(df)} patients -> {out_path}")


if __name__ == "__main__":
    main()
