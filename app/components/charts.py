"""Reusable Plotly chart helpers for the Streamlit dashboard."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def skills_bar_chart(df: pd.DataFrame) -> go.Figure:
    return px.bar(
        df,
        x="skill",
        y="mentions",
        color="pct_change",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        labels={"mentions": "Job Mentions", "skill": "Skill", "pct_change": "WoW %"},
    )


def companies_bar_chart(df: pd.DataFrame) -> go.Figure:
    return px.bar(
        df,
        x="jobs",
        y="company",
        orientation="h",
        color="jobs",
        color_continuous_scale="Blues",
        labels={"jobs": "Job Postings", "company": "Company"},
    )


def topic_line_chart(df: pd.DataFrame, top_n: int = 8) -> go.Figure:
    top_topics = df.groupby("topic")["articles"].sum().nlargest(top_n).index
    filtered = df[df["topic"].isin(top_topics)]
    return px.line(
        filtered,
        x="date",
        y="articles",
        color="topic",
        markers=True,
        labels={"articles": "Article Count", "date": "Date"},
    )
