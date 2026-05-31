"""Report viewer component — renders a markdown report with download option."""
from datetime import date

import streamlit as st


def render_report(content: str, report_date: date) -> None:
    st.markdown(content)
    st.divider()
    st.download_button(
        label="Download as Markdown",
        data=content,
        file_name=f"market_report_{report_date}.md",
        mime="text/markdown",
    )
