"""
Turn free-text trial eligibility criteria into structured constraints:
min/max age, sex, required conditions, excluded conditions.

Eligibility criteria text on ClinicalTrials.gov typically looks like:

    Inclusion Criteria:
    - Age 18 to 75 years
    - Diagnosis of Type 2 diabetes mellitus
    Exclusion Criteria:
    - Pregnant or breastfeeding
    - History of pancreatitis

This is a first-pass rule-based + NER extractor. A production version
would fine-tune a clinical NER model (e.g. scispaCy's en_ner_bc5cdr_md);
this implementation keeps the same interface so that swap is a drop-in
model change, not a rewrite.
"""
import re
from pathlib import Path

import pandas as pd

try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except Exception:  # model not downloaded / spaCy not installed
    _NLP = None

PROCESSED_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"

AGE_PATTERN = re.compile(r"(\d{1,3})\s*(?:years|yrs|y/o|years old)?\s*(?:to|-|–)\s*(\d{1,3})\s*years", re.I)
SINGLE_AGE_PATTERN = re.compile(r"(?:age|aged)\s*(\d{1,3})\+?", re.I)


def split_sections(criteria_text: str) -> tuple[str, str]:
    """Split raw criteria text into inclusion / exclusion blocks."""
    if not criteria_text:
        return "", ""
    lower = criteria_text.lower()
    excl_idx = lower.find("exclusion criteria")
    if excl_idx == -1:
        return criteria_text, ""
    return criteria_text[:excl_idx], criteria_text[excl_idx:]


def extract_age_range(criteria_text: str) -> tuple[int | None, int | None]:
    if not criteria_text:
        return None, None
    match = AGE_PATTERN.search(criteria_text)
    if match:
        return int(match.group(1)), int(match.group(2))
    single = SINGLE_AGE_PATTERN.search(criteria_text)
    if single:
        return int(single.group(1)), None
    return None, None


def extract_condition_mentions(text: str) -> list[str]:
    """Pull condition-like noun phrases from a block of text.

    Falls back to line-splitting (each bullet becomes a candidate mention)
    if spaCy isn't available -- keeps the pipeline runnable end to end
    even in stripped-down environments (e.g. CI, or the HF Space).
    """
    if not text:
        return []
    lines = [l.strip("-• ").strip() for l in text.split("\n") if l.strip()]
    lines = [l for l in lines if l and not l.lower().startswith(("inclusion", "exclusion"))]

    if _NLP is None:
        return lines[:10]

    mentions = []
    for line in lines[:10]:
        doc = _NLP(line)
        noun_chunks = [chunk.text for chunk in doc.noun_chunks]
        mentions.extend(noun_chunks or [line])
    return mentions


def extract_structured_criteria(row: pd.Series) -> dict:
    inclusion_text, exclusion_text = split_sections(row.get("eligibility_criteria", ""))
    min_age, max_age = extract_age_range(row.get("eligibility_criteria", ""))

    return {
        "nct_id": row.get("nct_id"),
        "min_age": min_age,
        "max_age": max_age,
        "sex": row.get("sex"),
        "required_conditions": extract_condition_mentions(inclusion_text),
        "excluded_conditions": extract_condition_mentions(exclusion_text),
    }


def main():
    trials_path = PROCESSED_DIR.parent / "raw" / "trials"
    parquet_files = list(trials_path.glob("*.parquet")) if trials_path.exists() else []
    if not parquet_files:
        print(f"No raw trial files found in {trials_path} -- run ingestion first.")
        return

    df = pd.concat([pd.read_parquet(p) for p in parquet_files], ignore_index=True)
    structured = df.apply(extract_structured_criteria, axis=1, result_type="expand")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "trial_criteria.parquet"
    structured.to_parquet(out_path, index=False)
    print(f"Extracted structured criteria for {len(structured)} trials -> {out_path}")


if __name__ == "__main__":
    main()
