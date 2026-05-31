from datetime import date

import streamlit as st
from langchain_core.messages import HumanMessage

st.title("🤖 Market Intelligence AI")
st.caption("Ask anything about the tech job market, trending skills, startup activity, or recent news.")

with st.expander("Example questions"):
    st.markdown("""
- *What are the top 5 trending skills this week?*
- *Which companies are hiring the most data engineers?*
- *What's happening in AI funding this week?*
- *Compare Python vs Go job postings this month*
- *What startups launched on ProductHunt today?*
- *Is demand for Kubernetes growing or declining?*
- *Summarize the top tech news from the last 3 days*
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask me anything about the market..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Querying database and thinking..."):
            try:
                from agent.graph import graph

                history = [
                    HumanMessage(content=m["content"])
                    if m["role"] == "user"
                    else m["content"]
                    for m in st.session_state.messages
                ]
                result = graph.invoke({"messages": [HumanMessage(content=prompt)]})
                answer = result["messages"][-1].content
            except Exception as e:
                answer = f"Sorry, I encountered an error: {e}\n\nMake sure `OPENAI_API_KEY` is set and the database is populated."

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

if st.session_state.messages:
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()
