import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="AI Market Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation(
    [
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
        st.Page("pages/chat.py", title="AI Chat", icon="🤖"),
        st.Page("pages/report.py", title="Daily Report", icon="📰"),
    ]
)
pg.run()
