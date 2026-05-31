"""LangGraph tools — safe read-only queries against the market intelligence DB."""
import logging

from langchain_core.tools import tool
from sqlalchemy import text

from db.models import get_db_connection

logger = logging.getLogger(__name__)

_ALLOWED_PREFIXES = ("select", "with", "explain")


def _safe_query(sql: str) -> str:
    """Execute a read-only SQL query; reject any write statements."""
    stripped = sql.strip().lower()
    if not any(stripped.startswith(p) for p in _ALLOWED_PREFIXES):
        return "Error: only SELECT / WITH / EXPLAIN queries are allowed."
    conn = get_db_connection()
    try:
        result = conn.execute(text(sql))
        rows = result.fetchmany(50)
        cols = list(result.keys())
        if not rows:
            return "No results found."
        header = " | ".join(cols)
        divider = "-" * len(header)
        lines = [header, divider] + [" | ".join(str(v) for v in row) for row in rows]
        return "\n".join(lines)
    except Exception as e:
        logger.error("DB query error: %s", e)
        return f"Query error: {e}"
    finally:
        conn.close()


@tool
def query_database(sql: str) -> str:
    """Execute a read-only SQL query against the market intelligence database.
    Tables available: raw_jobs, raw_articles, raw_startups, raw_github_trending,
    staging.stg_jobs, staging.stg_articles, staging.stg_startups,
    marts.trending_skills, marts.top_hiring_companies, marts.topic_volumes,
    marts.daily_snapshot, daily_reports.
    Use this for any custom question about jobs, skills, companies, or trends."""
    return _safe_query(sql)


@tool
def get_trending_skills(period: str = "week") -> str:
    """Get the top trending tech skills from job postings.
    period: 'week' (default), 'month'. Returns skill name, mention count, and % change."""
    if period == "month":
        interval = "28 days"
    else:
        interval = "7 days"

    sql = f"""
        SELECT skill_name, mention_count, pct_change
        FROM marts.trending_skills
        WHERE week_start >= CURRENT_DATE - INTERVAL '{interval}'
        ORDER BY mention_count DESC
        LIMIT 15
    """
    return _safe_query(sql)


@tool
def get_top_hiring_companies(role: str = "") -> str:
    """Get the companies posting the most jobs this week.
    Optionally filter by role keyword (e.g. 'data engineer', 'ml engineer')."""
    if role:
        where_clause = f"AND title ILIKE '%{role.replace(\"'\", \"''\")}%'"
    else:
        where_clause = ""

    sql = f"""
        SELECT company, COUNT(*) AS job_count,
               ARRAY_AGG(DISTINCT title ORDER BY title) AS sample_roles
        FROM staging.stg_jobs
        WHERE date_posted >= CURRENT_DATE - INTERVAL '7 days'
          AND company != 'Unknown'
          {where_clause}
        GROUP BY company
        ORDER BY job_count DESC
        LIMIT 10
    """
    return _safe_query(sql)


@tool
def summarize_recent_news(topic: str) -> str:
    """Fetch recent articles about a given topic from the last 7 days.
    Returns titles, summaries, and publication dates sorted by score."""
    safe_topic = topic.replace("'", "''")
    sql = f"""
        SELECT title, summary, source, published_at, score
        FROM staging.stg_articles
        WHERE (title ILIKE '%{safe_topic}%' OR summary ILIKE '%{safe_topic}%')
          AND article_date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY score DESC, published_at DESC
        LIMIT 8
    """
    return _safe_query(sql)
