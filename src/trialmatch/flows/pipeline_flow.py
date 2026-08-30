"""
Prefect flow that orchestrates the full pipeline: ingest -> ETL ->
data quality -> match -> load. Running this file end to end is the
single-command way to reproduce the whole project from scratch.

Each stage is a @task so failures, retries, and logs are visible per
stage in the Prefect UI (`prefect server start` + `prefect deploy`, or
just run this script directly for a local synchronous run).
"""
from prefect import flow, task

from trialmatch.ingestion.fetch_trials import fetch_trials
from trialmatch.ingestion.generate_patients import generate_fallback_patients, RAW_DIR as PATIENTS_RAW_DIR
from trialmatch.etl.parse_fhir import build_patient_table
from trialmatch.etl.extract_criteria import extract_structured_criteria
from trialmatch.etl.data_quality import QualityReport, check_patients, check_trial_criteria


@task(retries=2, retry_delay_seconds=10)
def ingest_trials(condition: str, max_studies: int):
    df = fetch_trials(condition, max_studies)
    return df


@task
def ingest_patients(count: int):
    generate_fallback_patients(count, PATIENTS_RAW_DIR)
    return build_patient_table()


@task
def extract_criteria(trials_df):
    return trials_df.apply(extract_structured_criteria, axis=1, result_type="expand")


@task
def run_quality_checks(patients_df, criteria_df):
    report = QualityReport()
    check_patients(patients_df, report)
    check_trial_criteria(criteria_df, report)
    print(report.summary())
    if report.failed():
        raise ValueError(f"Data quality checks failed: {report.failed()}")
    return report


@flow(name="trialmatch-pipeline")
def pipeline_flow(condition: str = "diabetes", max_studies: int = 100, patient_count: int = 200):
    trials_df = ingest_trials(condition, max_studies)
    patients_df = ingest_patients(patient_count)
    criteria_df = extract_criteria(trials_df)
    run_quality_checks(patients_df, criteria_df)
    print(f"Pipeline complete: {len(trials_df)} trials, {len(patients_df)} patients")


if __name__ == "__main__":
    pipeline_flow()
