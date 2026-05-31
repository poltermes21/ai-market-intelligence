-- Mart: trending tech skills extracted from job descriptions (last 4 weeks)
{{ config(materialized='table', schema='marts') }}

WITH job_descriptions AS (
    SELECT description, date_posted
    FROM {{ ref('stg_jobs') }}
    WHERE date_posted >= CURRENT_DATE - INTERVAL '28 days'
),
skills AS (
    SELECT unnest(ARRAY[
        'Python', 'SQL', 'Spark', 'Kafka', 'dbt', 'Airflow',
        'Docker', 'Kubernetes', 'AWS', 'GCP', 'Azure',
        'React', 'FastAPI', 'LangChain', 'PyTorch', 'TensorFlow',
        'Rust', 'Go', 'TypeScript', 'GraphQL', 'Scala',
        'Java', 'R', 'Snowflake', 'Databricks', 'MLOps'
    ]) AS skill_name
),
weekly_counts AS (
    SELECT
        DATE_TRUNC('week', jd.date_posted)::DATE   AS week_start,
        s.skill_name,
        COUNT(*) FILTER (
            WHERE jd.description ILIKE '%' || s.skill_name || '%'
        )                                          AS mention_count
    FROM job_descriptions jd
    CROSS JOIN skills s
    GROUP BY 1, 2
)
SELECT
    week_start,
    skill_name,
    mention_count,
    LAG(mention_count) OVER (
        PARTITION BY skill_name ORDER BY week_start
    )                                                           AS prev_week_count,
    ROUND(
        100.0 * (
            mention_count - LAG(mention_count) OVER (
                PARTITION BY skill_name ORDER BY week_start
            )
        ) / NULLIF(LAG(mention_count) OVER (
            PARTITION BY skill_name ORDER BY week_start
        ), 0),
        2
    )                                                           AS pct_change
FROM weekly_counts
ORDER BY week_start DESC, mention_count DESC
