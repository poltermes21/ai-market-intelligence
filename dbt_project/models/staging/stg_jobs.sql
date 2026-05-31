-- Staging view: clean and unify raw job postings
{{ config(materialized='view', schema='staging') }}

SELECT
    id,
    source,
    external_id,
    TRIM(title)                                         AS title,
    TRIM(COALESCE(company, 'Unknown'))                  AS company,
    TRIM(COALESCE(location, 'Remote'))                  AS location,
    COALESCE(description, '')                           AS description,
    salary_min,
    salary_max,
    COALESCE(currency, 'USD')                           AS currency,
    COALESCE(date_posted, DATE(ingested_at))            AS date_posted,
    url,
    ingested_at
FROM raw_jobs
WHERE title IS NOT NULL
  AND title != ''
