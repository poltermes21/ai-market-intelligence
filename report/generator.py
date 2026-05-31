"""Daily market intelligence report generator."""
import logging
import os
from datetime import date

from langchain_openai import ChatOpenAI
from sqlalchemy import text

from db.models import get_db_connection

logger = logging.getLogger(__name__)


def _fetch_snapshot_data(conn) -> dict:
    top_skills = conn.execute(text("""
        SELECT skill_name, mention_count, pct_change
        FROM marts.trending_skills
        WHERE week_start = DATE_TRUNC('week', CURRENT_DATE)::DATE
        ORDER BY mention_count DESC
        LIMIT 10
    """)).fetchall()

    top_companies = conn.execute(text("""
        SELECT company, job_count
        FROM marts.top_hiring_companies
        ORDER BY job_count DESC
        LIMIT 5
    """)).fetchall()

    top_articles = conn.execute(text("""
        SELECT title, url, score, source
        FROM staging.stg_articles
        WHERE article_date = CURRENT_DATE
        ORDER BY score DESC
        LIMIT 5
    """)).fetchall()

    top_startups = conn.execute(text("""
        SELECT name, tagline, votes
        FROM staging.stg_startups
        WHERE launch_date = CURRENT_DATE
        ORDER BY votes DESC
        LIMIT 5
    """)).fetchall()

    top_github = conn.execute(text("""
        SELECT repo_name, language, stars, description
        FROM raw_github_trending
        WHERE trending_date = CURRENT_DATE
        ORDER BY stars DESC
        LIMIT 5
    """)).fetchall()

    return {
        "top_skills": top_skills,
        "top_companies": top_companies,
        "top_articles": top_articles,
        "top_startups": top_startups,
        "top_github": top_github,
    }


def _build_prompt(data: dict, today: date) -> str:
    skills_txt = "\n".join(
        f"  - {s[0]}: {s[1]} mentions"
        + (f" ({'+' if (s[2] or 0) >= 0 else ''}{s[2]}% WoW)" if s[2] is not None else "")
        for s in data["top_skills"]
    ) or "  No data yet."

    companies_txt = "\n".join(
        f"  - {c[0]}: {c[1]} jobs" for c in data["top_companies"]
    ) or "  No data yet."

    articles_txt = "\n".join(
        f"  - [{a[0]}]({a[1]}) — {a[3]} (score: {a[2]})"
        for a in data["top_articles"]
    ) or "  No data yet."

    startups_txt = "\n".join(
        f"  - **{s[0]}**: {s[1]} ({s[2]} votes)" for s in data["top_startups"]
    ) or "  No data yet."

    github_txt = "\n".join(
        f"  - [{g[0]}](https://github.com/{g[0]}) [{g[1]}] — {g[2]:,} stars — {g[3]}"
        for g in data["top_github"]
    ) or "  No data yet."

    return f"""You are a senior market intelligence analyst. Write a concise, insightful daily briefing
for {today.strftime('%A, %B %d %Y')} using the data provided below.

Format it as a professional markdown report. Use these exact section headers and be analytical —
highlight trends, growth signals, and notable patterns. Be specific and data-driven.

## 🔥 Trending Skills
{skills_txt}

## 🏢 Top Hiring Companies
{companies_txt}

## 📰 Top Tech News
{articles_txt}

## 🚀 Hot Startups (ProductHunt)
{startups_txt}

## 💻 GitHub Trending
{github_txt}

Write the report now. Start with a 2-sentence executive summary, then expand each section.
Keep the total report under 600 words.
"""


def generate_daily_report() -> str:
    today = date.today()
    conn = get_db_connection()
    try:
        data = _fetch_snapshot_data(conn)
    finally:
        conn.close()

    prompt = _build_prompt(data, today)

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.3,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    response = llm.invoke(prompt)
    report_text = response.content

    conn = get_db_connection()
    try:
        conn.execute(
            text("""
                INSERT INTO daily_reports (report_date, content)
                VALUES (:report_date, :content)
                ON CONFLICT (report_date) DO UPDATE SET content = EXCLUDED.content
            """),
            {"report_date": today, "content": report_text},
        )
        conn.commit()
        logger.info("Daily report saved for %s", today)
    finally:
        conn.close()

    return report_text


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(generate_daily_report())
