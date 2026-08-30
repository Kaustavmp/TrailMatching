-- Cast and clean the raw patients table loaded from the ETL layer.
select
    patient_id,
    lower(gender) as gender,
    birthdate::date as birthdate,
    date_part('year', age(current_date, birthdate::date)) as age,
    conditions
from {{ source('raw', 'patients') }}
where patient_id is not null
