from datetime import date, timedelta

import streamlit as st
from sqlalchemy import text

from db.models import get_db_connection

st.title("📰 Daily Market Intelligence Report")
st.caption("Auto-generated every morning at 10:00 UTC by the AI analyst.")


@st.cache_data(ttl=60)
def load_report_dates() -> list[date]:
    try:
        with get_db_connection() as conn:
            rows = conn.execute(text("""
                SELECT report_date FROM daily_reports
                ORDER BY report_date DESC
                LIMIT 30
            """)).fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


def load_report(report_date: date) -> str | None:
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                text("SELECT content FROM daily_reports WHERE report_date = :d"),
                {"d": report_date},
            ).fetchone()
        return row[0] if row else None
    except Exception:
        return None


dates = load_report_dates()

if not dates:
    st.info("No reports generated yet. The `daily_report` DAG runs daily at 10:00 UTC, or you can trigger it manually from the Airflow UI.")

    st.subheader("Generate a Report Now")
    if st.button("Generate Today's Report"):
        with st.spinner("Generating report (this may take ~30 seconds)..."):
            try:
                from report.generator import generate_daily_report
                report_text = generate_daily_report()
                st.success("Report generated!")
                st.markdown(report_text)
            except Exception as e:
                st.error(f"Failed to generate report: {e}")
else:
    selected_date = st.selectbox(
        "Select report date",
        options=dates,
        format_func=lambda d: d.strftime("%A, %B %d %Y"),
    )

    report = load_report(selected_date)
    if report:
        st.markdown(report)
        st.divider()
        st.download_button(
            label="Download as Markdown",
            data=report,
            file_name=f"market_report_{selected_date}.md",
            mime="text/markdown",
        )
    else:
        st.warning("Could not load report content.")

    st.divider()
    st.subheader("Generate a Fresh Report")
    if st.button("Re-generate Today's Report"):
        with st.spinner("Generating..."):
            try:
                from report.generator import generate_daily_report
                report_text = generate_daily_report()
                st.success("Done!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")
