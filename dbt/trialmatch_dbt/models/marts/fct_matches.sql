-- One row per (patient, trial) pair that was scored by the matching
-- engine. This is what the FastAPI /match endpoint and the HF Space
-- demo both read from.
select
    m.patient_id,
    m.nct_id,
    m.eligible,
    m.similarity_score,
    m.exclusion_reasons,
    p.age,
    p.gender,
    tr.brief_title
from {{ source('raw', 'matches') }} m
left join {{ ref('stg_patients') }} p using (patient_id)
left join {{ ref('stg_trials') }} tr using (nct_id)
