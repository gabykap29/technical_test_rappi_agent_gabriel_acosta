"""Streamlit app for the Rappi operations intelligence agent."""

from __future__ import annotations

import streamlit as st

from rappi_intelligence.agent import RappiOperationsAgent
from rappi_intelligence.models import AgentResponse
from rappi_intelligence.reporting import render_markdown_report


@st.cache_resource
def _agent() -> RappiOperationsAgent:
    return RappiOperationsAgent()


def _quick_questions() -> dict[str, list[str]]:
    return {
        "Rankings": [
            "Cuales son las 5 zonas con mayor Lead Penetration esta semana?",
            "Cuales son las 5 zonas con menor Perfect Order esta semana?",
        ],
        "Comparaciones": [
            "Compara Perfect Order entre zonas Wealthy y Non Wealthy en Mexico",
            "Cual es el promedio de Lead Penetration por pais?",
        ],
        "Diagnostico": [
            "Que zonas tienen alto Lead Penetration pero bajo Perfect Order?",
            "Cuales zonas problematicas hay esta semana?",
        ],
        "Tendencias": [
            "Muestra la evolucion de Gross Profit UE en Chapinero ultimas 8 semanas",
            "Cuales zonas crecen mas en ordenes en las ultimas 5 semanas?",
        ],
    }


def main() -> None:
    st.set_page_config(
        page_title="Rappi Operations Intelligence",
        page_icon="R",
        layout="wide",
    )
    _inject_styles()

    agent = _agent()
    _init_state()

    _render_sidebar(agent)
    _render_header()
    _render_dataset_overview(agent)

    analysis_tab, report_tab, help_tab = st.tabs(
        ["Ask the agent", "Executive report", "Demo guide"]
    )

    with analysis_tab:
        _render_agent_workspace(agent)

    with report_tab:
        st.markdown("### Executive report")
        st.caption(
            "Auto-generated from anomalies, trends, benchmarks and opportunities."
        )
        if st.button("Generate report now", type="primary"):
            st.session_state["report"] = render_markdown_report(agent.dataset)
        if st.session_state.get("report"):
            st.markdown(st.session_state["report"])
        else:
            st.info("Generate the report when you want to review executive insights.")

    with help_tab:
        _render_demo_guide()


def _init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("pending_question", None)
    st.session_state.setdefault("report", None)


def _render_header() -> None:
    st.markdown(
        """
        <section class="app-header">
            <div>
                <p class="eyebrow">Operations analytics agent</p>
                <h1>Rappi Operations Intelligence</h1>
                <p class="header-copy">
                    Ask business questions, inspect the evidence and generate an
                    executive readout from the same operational dataset.
                </p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar(agent: RappiOperationsAgent) -> None:
    with st.sidebar:
        st.markdown("## Quick actions")
        if st.button("Clear conversation", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["pending_question"] = None
        if st.button("Prepare executive report", use_container_width=True):
            st.session_state["report"] = render_markdown_report(agent.dataset)

        st.divider()
        st.markdown("## Demo questions")
        for group, questions in _quick_questions().items():
            with st.expander(group, expanded=group == "Rankings"):
                for question in questions:
                    if st.button(question, key=f"quick-{group}-{question}"):
                        st.session_state["pending_question"] = question

        st.divider()
        st.caption(
            "Tip: use follow-up questions after selecting a metric. The agent keeps "
            "the latest metric, country and zone in memory."
        )


def _render_dataset_overview(agent: RappiOperationsAgent) -> None:
    wide = agent.dataset.wide
    countries = wide["COUNTRY"].nunique()
    zones = wide["ZONE"].nunique()
    metrics = wide["METRIC"].nunique()
    rows = len(wide)

    cols = st.columns(4)
    cols[0].metric("Countries", countries)
    cols[1].metric("Zones", zones)
    cols[2].metric("Metrics", metrics)
    cols[3].metric("Analytical rows", f"{rows:,}")


def _render_agent_workspace(agent: RappiOperationsAgent) -> None:
    left, right = st.columns([0.62, 0.38], gap="large")

    with left:
        st.markdown("### Conversation")
        st.caption("Use natural language. The answer includes evidence, not only text.")

        question = st.chat_input(
            "Ask about rankings, trends, comparisons or problematic zones"
        )
        question = st.session_state.pop("pending_question", None) or question

        if question:
            response = agent.ask(question)
            st.session_state["messages"].append(
                {"question": question, "response": response}
            )

        if not st.session_state["messages"]:
            st.info("Start with a demo question from the sidebar or type your own.")
        for item in st.session_state["messages"]:
            with st.chat_message("user"):
                st.write(item["question"])
            with st.chat_message("assistant"):
                _render_response(item["response"])

    with right:
        st.markdown("### Suggested path")
        st.markdown(
            """
            1. Start with a ranking to find relevant zones.
            2. Compare Wealthy vs Non Wealthy segments.
            3. Check a trend for one zone.
            4. Generate the executive report.
            """
        )
        st.markdown("### What the agent can answer")
        st.write("- Top and bottom zones by metric")
        st.write("- Comparisons by country and zone type")
        st.write("- Weekly trends from L8W to L0W")
        st.write("- High/low multivariable diagnosis")
        st.write("- Orders growth and possible drivers")


def _render_response(response: AgentResponse) -> None:
    st.markdown(response.answer)

    evidence_tab, chart_tab, next_tab = st.tabs(["Evidence", "Chart", "Next"])

    with evidence_tab:
        if response.table is not None and not response.table.empty:
            st.dataframe(response.table, use_container_width=True, hide_index=True)
        else:
            st.info("No table was returned for this question.")

    with chart_tab:
        if response.chart is not None:
            st.plotly_chart(response.chart, use_container_width=True)
        else:
            st.info("This answer does not need a chart.")

    with next_tab:
        if response.suggestions:
            for index, suggestion in enumerate(response.suggestions):
                if st.button(
                    suggestion,
                    key=f"suggestion-{hash(response.answer)}-{index}",
                ):
                    st.session_state["pending_question"] = suggestion
                    st.rerun()
        else:
            st.write("Ask another question or generate the executive report.")


def _render_demo_guide() -> None:
    st.markdown("### Demo script")
    st.write("Use this flow for a short live presentation:")
    st.write("1. Show dataset coverage at the top.")
    st.write("2. Ask for top Lead Penetration zones.")
    st.write("3. Compare Perfect Orders in Mexico by zone type.")
    st.write("4. Show Gross Profit UE trend in Chapinero.")
    st.write("5. Ask for high Lead Penetration and low Perfect Orders.")
    st.write("6. Generate the executive report.")

    st.markdown("### Positioning")
    st.write(
        "The system is deterministic: it avoids hallucinations, keeps cost at zero "
        "and makes every answer auditable through tables and charts."
    )


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.8rem;
                padding-bottom: 3rem;
            }
            .app-header {
                background: linear-gradient(135deg, #f8faf9 0%, #edf7f1 100%);
                border: 1px solid #d7e7dc;
                border-radius: 8px;
                padding: 1.4rem 1.6rem;
                margin-bottom: 1rem;
            }
            .eyebrow {
                color: #16784a;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0;
                margin-bottom: 0.2rem;
                text-transform: uppercase;
            }
            .app-header h1 {
                color: #202423;
                font-size: 2rem;
                margin: 0;
            }
            .header-copy {
                color: #4f5b56;
                font-size: 1rem;
                margin: 0.4rem 0 0;
                max-width: 760px;
            }
            div[data-testid="stMetric"] {
                background: #ffffff;
                border: 1px solid #dce5df;
                border-radius: 8px;
                padding: 0.8rem;
            }
            div.stButton > button {
                border-radius: 8px;
                border-color: #c7d8ce;
            }
            div.stButton > button:hover {
                border-color: #16784a;
                color: #16784a;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
