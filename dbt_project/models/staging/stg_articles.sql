-- Staging view: clean and unify raw articles from all sources
{{ config(materialized='view', schema='staging') }}

SELECT
    id,
    source,
    external_id,
    TRIM(title)                                         AS title,
    TRIM(COALESCE(summary, ''))                         AS summary,
    url,
    published_at,
    COALESCE(score, 0)                                  AS score,
    COALESCE(num_comments, 0)                           AS num_comments,
    DATE(COALESCE(published_at, ingested_at))           AS article_date,
    ingested_at
FROM raw_articles
WHERE title IS NOT NULL
  AND title != ''
