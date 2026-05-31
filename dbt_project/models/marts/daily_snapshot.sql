-- Mart: daily snapshot aggregating top signals for the report
{{ config(materialized='table', schema='marts') }}

WITH top_skills AS (
    SELECT ARRAY_AGG(skill_name ORDER BY mention_count DESC) AS skills
    FROM {{ ref('trending_skills') }}
    WHERE week_start = DATE_TRUNC('week', CURRENT_DATE)::DATE
    LIMIT 1
),
top_companies AS (
    SELECT ARRAY_AGG(company ORDER BY job_count DESC) AS companies
    FROM {{ ref('top_hiring_companies') }}
    LIMIT 1
),
top_articles AS (
    SELECT ARRAY_AGG(
        title || ' (' || source || ')' ORDER BY score DESC
    ) AS articles
    FROM {{ ref('stg_articles') }}
    WHERE article_date = CURRENT_DATE
    LIMIT 1
),
top_startups AS (
    SELECT ARRAY_AGG(
        name || ': ' || tagline ORDER BY votes DESC
    ) AS startups
    FROM {{ ref('stg_startups') }}
    WHERE launch_date = CURRENT_DATE
    LIMIT 1
)
SELECT
    CURRENT_DATE                        AS snapshot_date,
    COALESCE(ts.skills, ARRAY[]::TEXT[])      AS top_skills,
    COALESCE(tc.companies, ARRAY[]::TEXT[])   AS top_companies,
    COALESCE(ta.articles, ARRAY[]::TEXT[])    AS top_articles,
    COALESCE(tst.startups, ARRAY[]::TEXT[])   AS top_startups
FROM top_skills ts
CROSS JOIN top_companies tc
CROSS JOIN top_articles ta
CROSS JOIN top_startups tst
