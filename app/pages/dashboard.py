import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

from db.models import get_db_connection

st.title("📊 Market Intelligence Dashboard")
st.caption("Real-time signals from job boards, tech news, startups, and GitHub.")

conn = get_db_connection()


@st.cache_data(ttl=300)
def load_trending_skills():
    with get_db_connection() as c:
        rows = c.execute(text("""
            SELECT skill_name, mention_count, pct_change, week_start
            FROM marts.trending_skills
            WHERE week_start = DATE_TRUNC('week', CURRENT_DATE)::DATE
            ORDER BY mention_count DESC
            LIMIT 20
        """)).fetchall()
    return pd.DataFrame(rows, columns=["skill", "mentions", "pct_change", "week_start"])


@st.cache_data(ttl=300)
def load_top_companies():
    with get_db_connection() as c:
        rows = c.execute(text("""
            SELECT company, job_count
            FROM marts.top_hiring_companies
            ORDER BY job_count DESC
            LIMIT 15
        """)).fetchall()
    return pd.DataFrame(rows, columns=["company", "jobs"])


@st.cache_data(ttl=300)
def load_topic_volumes():
    with get_db_connection() as c:
        rows = c.execute(text("""
            SELECT topic, date, article_count, avg_score
            FROM marts.topic_volumes
            ORDER BY date DESC, article_count DESC
        """)).fetchall()
    return pd.DataFrame(rows, columns=["topic", "date", "articles", "avg_score"])


@st.cache_data(ttl=300)
def load_recent_articles():
    with get_db_connection() as c:
        rows = c.execute(text("""
            SELECT title, source, score, url, article_date
            FROM staging.stg_articles
            ORDER BY article_date DESC, score DESC
            LIMIT 20
        """)).fetchall()
    return pd.DataFrame(rows, columns=["title", "source", "score", "url", "date"])


@st.cache_data(ttl=300)
def load_github_trending():
    with get_db_connection() as c:
        rows = c.execute(text("""
            SELECT repo_name, language, stars, forks, description, trending_date
            FROM raw_github_trending
            WHERE trending_date = CURRENT_DATE
            ORDER BY stars DESC
            LIMIT 20
        """)).fetchall()
    return pd.DataFrame(rows, columns=["repo", "language", "stars", "forks", "description", "date"])


# --- KPI row ---
col1, col2, col3, col4 = st.columns(4)

try:
    with get_db_connection() as c:
        total_jobs = c.execute(text("SELECT COUNT(*) FROM raw_jobs WHERE date_posted >= CURRENT_DATE - 7")).scalar()
        total_articles = c.execute(text("SELECT COUNT(*) FROM raw_articles WHERE ingested_at >= NOW() - INTERVAL '24 hours'")).scalar()
        total_startups = c.execute(text("SELECT COUNT(*) FROM raw_startups WHERE launch_date = CURRENT_DATE")).scalar()
        total_repos = c.execute(text("SELECT COUNT(*) FROM raw_github_trending WHERE trending_date = CURRENT_DATE")).scalar()

    col1.metric("Jobs (7 days)", f"{total_jobs:,}")
    col2.metric("Articles (24h)", f"{total_articles:,}")
    col3.metric("Startups Today", f"{total_startups:,}")
    col4.metric("Trending Repos", f"{total_repos:,}")
except Exception as e:
    st.warning(f"Database not yet populated — run the Airflow DAGs first. ({e})")

st.divider()

# --- Trending Skills ---
st.subheader("🔥 Trending Skills This Week")
try:
    skills_df = load_trending_skills()
    if not skills_df.empty:
        fig = px.bar(
            skills_df,
            x="skill",
            y="mentions",
            color="pct_change",
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
            labels={"mentions": "Job Mentions", "skill": "Skill", "pct_change": "WoW %"},
            title="Skills ranked by job posting mentions (colour = week-over-week change)",
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No skill data yet — run adzuna_jobs_ingestion DAG first.")
except Exception as e:
    st.error(f"Could not load skill data: {e}")

# --- Top Hiring Companies ---
st.subheader("🏢 Top Hiring Companies (Last 7 Days)")
try:
    companies_df = load_top_companies()
    if not companies_df.empty:
        fig2 = px.bar(
            companies_df,
            x="jobs",
            y="company",
            orientation="h",
            labels={"jobs": "Job Postings", "company": "Company"},
            color="jobs",
            color_continuous_scale="Blues",
        )
        fig2.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No company data yet.")
except Exception as e:
    st.error(f"Could not load company data: {e}")

# --- Topic Volumes ---
st.subheader("📈 Topic Buzz (Last 14 Days)")
try:
    topics_df = load_topic_volumes()
    if not topics_df.empty:
        top_topics = topics_df.groupby("topic")["articles"].sum().nlargest(8).index.tolist()
        filtered = topics_df[topics_df["topic"].isin(top_topics)]
        fig3 = px.line(
            filtered,
            x="date",
            y="articles",
            color="topic",
            markers=True,
            labels={"articles": "Article Count", "date": "Date", "topic": "Topic"},
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No topic data yet.")
except Exception as e:
    st.error(f"Could not load topic data: {e}")

# --- Two-column bottom ---
left, right = st.columns(2)

with left:
    st.subheader("📰 Latest Articles")
    try:
        articles_df = load_recent_articles()
        if not articles_df.empty:
            for _, row in articles_df.head(8).iterrows():
                st.markdown(f"**[{row['title']}]({row['url']})** — *{row['source']}* (score: {row['score']})")
        else:
            st.info("No articles yet.")
    except Exception as e:
        st.error(f"Could not load articles: {e}")

with right:
    st.subheader("💻 GitHub Trending Today")
    try:
        github_df = load_github_trending()
        if not github_df.empty:
            for _, row in github_df.head(8).iterrows():
                st.markdown(
                    f"**[{row['repo']}](https://github.com/{row['repo']})** "
                    f"`{row['language']}` — ⭐ {row['stars']:,} — {row['description'][:80]}"
                )
        else:
            st.info("No GitHub data yet.")
    except Exception as e:
        st.error(f"Could not load GitHub data: {e}")
