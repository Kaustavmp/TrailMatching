.PHONY: up down ingest etl dbt match api test pipeline

up:
	docker compose up -d postgres

down:
	docker compose down

ingest:
	python -m trialmatch.ingestion.fetch_trials --condition "breast cancer" --max-studies 200
	python -m trialmatch.ingestion.generate_patients --count 500

etl:
	python -m trialmatch.etl.parse_fhir
	python -m trialmatch.etl.extract_criteria
	python -m trialmatch.etl.data_quality

dbt:
	cd dbt/trialmatch_dbt && dbt run

match:
	python -m trialmatch.matching.rules_engine
	python -m trialmatch.matching.embeddings

api:
	uvicorn trialmatch.api.main:app --reload

test:
	pytest tests/

pipeline:
	python -m trialmatch.flows.pipeline_flow
