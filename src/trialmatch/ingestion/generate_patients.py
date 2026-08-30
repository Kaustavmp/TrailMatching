"""
Generate synthetic patient records with Synthea and load them into raw storage.

Synthea (https://github.com/synthetichealth/synthea) is a Java tool that
produces realistic, fully synthetic patient records in FHIR format --
there is zero real PHI involved, which is what makes this project safe to
build and demo publicly.

This script shells out to a local Synthea build. If Synthea isn't
available (e.g. quick local testing without Java), it falls back to a
lightweight synthetic generator so the rest of the pipeline still has
data to run against -- clearly flagged as fallback data, never presented
as equivalent to Synthea's clinically-informed models.
"""
import argparse
import json
import random
import subprocess
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw" / "patients"
SYNTHEA_JAR = Path(__file__).resolve().parents[3] / "synthea" / "synthea-with-dependencies.jar"

CONDITIONS_POOL = [
    "Breast cancer", "Type 2 diabetes mellitus", "Hypertension",
    "Asthma", "Major depressive disorder", "Rheumatoid arthritis",
]


def run_synthea(count: int, out_dir: Path):
    if not SYNTHEA_JAR.exists():
        raise FileNotFoundError(
            f"Synthea jar not found at {SYNTHEA_JAR}. "
            "Download it from https://github.com/synthetichealth/synthea/releases "
            "or use --fallback for a quick local stand-in."
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["java", "-jar", str(SYNTHEA_JAR), "-p", str(count), "--exporter.fhir.export", "true",
         "--exporter.baseDirectory", str(out_dir)],
        check=True,
    )


def generate_fallback_patients(count: int, out_dir: Path):
    """Minimal synthetic FHIR-*like* bundles for local testing without Java."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        patient_id = f"fallback-{i:05d}"
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {"resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "gender": random.choice(["male", "female"]),
                    "birthDate": f"{random.randint(1940, 2005)}-01-01",
                }},
                {"resource": {
                    "resourceType": "Condition",
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "code": {"text": random.choice(CONDITIONS_POOL)},
                }},
            ],
        }
        with open(out_dir / f"{patient_id}.json", "w") as f:
            json.dump(bundle, f)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic patient records")
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--fallback", action="store_true",
                         help="Skip Synthea, use a lightweight local generator instead")
    args = parser.parse_args()

    if args.fallback:
        generate_fallback_patients(args.count, RAW_DIR)
        print(f"Wrote {args.count} fallback patient bundles to {RAW_DIR}")
    else:
        run_synthea(args.count, RAW_DIR)
        print(f"Synthea wrote {args.count} patient bundles to {RAW_DIR}")


if __name__ == "__main__":
    main()
