"""Streamlit app for the Rappi operations intelligence agent."""

from __future__ import annotations

import streamlit as st

from rappi_intelligence.agent import RappiOperationsAgent
from rappi_intelligence.reporting import render_markdown_report


@st.cache_resource
def _agent() -> RappiOperationsAgent:
    return RappiOperationsAgent()


def main() -> None:
    st.set_page_config(page_title="Rappi Operations Intelligence", layout="wide")
    st.title("Rappi Operations Intelligence")

    agent = _agent()

    with st.sidebar:
        st.header("Starter questions")
        for question in agent.starter_questions():
            if st.button(question, use_container_width=True):
                st.session_state["question"] = question
        st.divider()
        show_report = st.button("Generate executive report", use_container_width=True)

    if show_report:
        st.subheader("Executive Report")
        st.markdown(render_markdown_report(agent.dataset))
        return

    question = st.text_input(
        "Ask an operations question",
        value=st.session_state.get("question", ""),
        placeholder="Cuales son las 5 zonas con mayor Lead Penetration esta semana?",
    )
    if question:
        response = agent.ask(question)
        st.markdown(response.answer)
        if response.table is not None and not response.table.empty:
            st.dataframe(response.table, use_container_width=True)
        if response.chart is not None:
            st.plotly_chart(response.chart, use_container_width=True)
        if response.suggestions:
            st.subheader("Suggested next questions")
            for suggestion in response.suggestions:
                st.write(f"- {suggestion}")


if __name__ == "__main__":
    main()
