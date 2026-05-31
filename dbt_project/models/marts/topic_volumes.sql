-- Mart: article volume and engagement by topic per day (last 14 days)
{{ config(materialized='table', schema='marts') }}

WITH topics AS (
    SELECT unnest(ARRAY[
        'AI', 'machine learning', 'LLM', 'GPT', 'startup',
        'funding', 'open source', 'Python', 'cloud', 'security',
        'data engineering', 'Kubernetes', 'blockchain', 'SaaS', 'API'
    ]) AS topic
),
article_topics AS (
    SELECT
        a.article_date                              AS date,
        t.topic,
        COUNT(*)                                    AS article_count,
        AVG(a.score)                                AS avg_score
    FROM {{ ref('stg_articles') }} a
    CROSS JOIN topics t
    WHERE a.article_date >= CURRENT_DATE - INTERVAL '14 days'
      AND (
          a.title ILIKE '%' || t.topic || '%'
          OR a.summary ILIKE '%' || t.topic || '%'
      )
    GROUP BY 1, 2
)
SELECT *
FROM article_topics
ORDER BY date DESC, article_count DESC
