"""
TrialMatch — Streamlit demo (Hugging Face Space)

Loads a small bundled sample of synthetic patients/trials and runs the
real hard-filter matching logic live, so this demo genuinely computes
results rather than just displaying static output.
"""
import ast

import pandas as pd
import streamlit as st

from matching_logic import apply_hard_filters, relevance_score

st.set_page_config(page_title="TrialMatch", page_icon="🧬", layout="wide")


@st.cache_data
def load_data():
    patients = pd.read_csv("data/demo_patients.csv")
    trials = pd.read_csv("data/demo_trials.csv")

    for col in ["conditions"]:
        patients[col] = patients[col].apply(ast.literal_eval)
    for col in ["conditions", "required_conditions", "excluded_conditions"]:
        trials[col] = trials[col].apply(ast.literal_eval)

    return patients, trials


patients_df, trials_df = load_data()

st.title("🧬 TrialMatch")
st.caption(
    "Explainable clinical trial matching, running live against a synthetic sample dataset. "
    "Every recommendation ships with the reasons behind it — no black box."
)

with st.expander("ℹ️ About this demo", expanded=False):
    st.markdown(
        "This Space runs the **hard-filter matching logic** from the full pipeline "
        "directly in your browser session, against 25 synthetic patients and 20 synthetic "
        "trials bundled with this Space. All data is synthetic — no real patient "
        "information is used anywhere in this project.\n\n"
        "The full pipeline — real ClinicalTrials.gov ingestion, Synthea-generated patients, "
        "Prefect orchestration, dbt modeling, and sentence-transformer semantic ranking — "
        "lives in the companion [GitHub repository](https://github.com/your-username/trialmatch)."
    )

# ---- Sidebar: patient selector ----
st.sidebar.header("Select a patient")
patient_labels = patients_df.apply(
    lambda r: f"{r['display_name']} — {r['age']}y {r['gender']}", axis=1
)
selected_idx = st.sidebar.selectbox(
    "Synthetic patient", options=patients_df.index, format_func=lambda i: patient_labels[i]
)
patient = patients_df.loc[selected_idx].to_dict()

st.sidebar.markdown("**Recorded conditions**")
for c in patient["conditions"]:
    st.sidebar.markdown(f"- {c}")

# ---- Main: run matching live ----
st.subheader(f"Trial matches for {patient['display_name']}")

results = []
for _, trial in trials_df.iterrows():
    trial_dict = trial.to_dict()
    filter_result = apply_hard_filters(patient, trial_dict)
    score = relevance_score(patient, trial_dict) if filter_result.eligible else None
    results.append({
        "nct_id": trial_dict["nct_id"],
        "brief_title": trial_dict["brief_title"],
        "eligible": filter_result.eligible,
        "reasons": filter_result.reasons,
        "score": score,
    })

results_df = pd.DataFrame(results)
eligible_df = results_df[results_df.eligible].sort_values("score", ascending=False)
ineligible_df = results_df[~results_df.eligible]

col1, col2 = st.columns(2)
col1.metric("Eligible trials", len(eligible_df))
col2.metric("Not eligible", len(ineligible_df))

st.markdown("### ✅ Eligible, ranked by relevance")
if eligible_df.empty:
    st.info("No eligible trials in the sample set for this patient.")
else:
    for _, row in eligible_df.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{row['brief_title']}**  \n`{row['nct_id']}`")
            c2.metric("Relevance", f"{row['score']:.2f}")

st.markdown("### 🚫 Not eligible — with reasons")
if ineligible_df.empty:
    st.info("No excluded trials in the sample set for this patient.")
else:
    for _, row in ineligible_df.iterrows():
        with st.expander(f"{row['brief_title']} — `{row['nct_id']}`"):
            for reason in row["reasons"]:
                st.markdown(f"- {reason}")

st.divider()
st.caption(
    "Built as an end-to-end data engineering + NLP project. "
    "See the [GitHub repo](https://github.com/your-username/trialmatch) for the full "
    "ingestion → ETL → dbt → matching → API pipeline this demo is a lightweight window into."
)
