"""SQLAlchemy ORM models for the warehouse's raw/staging load layer.

dbt owns the transformation logic on top of these tables (see
dbt/trialmatch_dbt/models) -- this module is only responsible for getting
cleaned data safely into Postgres.
"""
from sqlalchemy import Column, String, Integer, Float, JSON, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String, primary_key=True)
    gender = Column(String)
    birthdate = Column(String)
    conditions = Column(JSON)
    medications = Column(JSON)


class Trial(Base):
    __tablename__ = "trials"

    nct_id = Column(String, primary_key=True)
    brief_title = Column(String)
    overall_status = Column(String)
    conditions = Column(JSON)
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)
    sex = Column(String, nullable=True)
    required_conditions = Column(JSON)
    excluded_conditions = Column(JSON)


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"))
    nct_id = Column(String, ForeignKey("trials.nct_id"))
    eligible = Column(Boolean)
    similarity_score = Column(Float, nullable=True)
    exclusion_reasons = Column(JSON)
