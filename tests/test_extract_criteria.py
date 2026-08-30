import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trialmatch.etl.extract_criteria import extract_age_range, split_sections

SAMPLE = """Inclusion Criteria:
- Age 18 to 75 years
- Diagnosis of Type 2 diabetes mellitus
Exclusion Criteria:
- Pregnant or breastfeeding
- History of pancreatitis
"""


def test_split_sections():
    inclusion, exclusion = split_sections(SAMPLE)
    assert "Diagnosis of Type 2 diabetes" in inclusion
    assert "pancreatitis" in exclusion.lower()


def test_extract_age_range():
    min_age, max_age = extract_age_range(SAMPLE)
    assert min_age == 18
    assert max_age == 75


def test_extract_age_range_handles_missing_text():
    assert extract_age_range("") == (None, None)
    assert extract_age_range(None) == (None, None)
