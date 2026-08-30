-- Cast and clean the raw trials + extracted-criteria tables.
select
    t.nct_id,
    t.brief_title,
    t.overall_status,
    t.conditions,
    c.min_age,
    c.max_age,
    c.sex,
    c.required_conditions,
    c.excluded_conditions
from {{ source('raw', 'trials') }} t
left join {{ source('raw', 'trial_criteria') }} c using (nct_id)
where t.nct_id is not null
