-- Mart: companies with the most job postings in the last 7 days
{{ config(materialized='table', schema='marts') }}

WITH recent_jobs AS (
    SELECT
        company,
        title,
        location,
        date_posted
    FROM {{ ref('stg_jobs') }}
    WHERE date_posted >= CURRENT_DATE - INTERVAL '7 days'
      AND company != 'Unknown'
),
company_stats AS (
    SELECT
        company,
        COUNT(*)                                    AS job_count,
        ARRAY_AGG(DISTINCT title ORDER BY title)    AS top_roles,
        ARRAY_AGG(DISTINCT location ORDER BY location) AS locations,
        DATE_TRUNC('week', CURRENT_DATE)::DATE      AS week_start
    FROM recent_jobs
    GROUP BY company
)
SELECT *
FROM company_stats
ORDER BY job_count DESC
