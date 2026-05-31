-- Staging view: clean and unify raw startup launches
{{ config(materialized='view', schema='staging') }}

SELECT
    id,
    source,
    external_id,
    TRIM(name)                                          AS name,
    TRIM(COALESCE(tagline, ''))                         AS tagline,
    TRIM(COALESCE(description, ''))                     AS description,
    COALESCE(topics, ARRAY[]::TEXT[])                   AS topics,
    COALESCE(votes, 0)                                  AS votes,
    COALESCE(launch_date, DATE(ingested_at))            AS launch_date,
    url,
    ingested_at
FROM raw_startups
WHERE name IS NOT NULL
  AND name != ''
