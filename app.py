import json
import streamlit as st

from productscout_agent import run_productscout


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="ProductScout AI",
    page_icon="🔎",
    layout="wide"
)


# =========================================================
# HEADER
# =========================================================

st.title("🔎 ProductScout AI")

st.subheader(
    "Agentic Product Research Assistant"
)

st.write(
    """
    ProductScout combines internal product metrics,
    customer feedback, and current web research to
    investigate product problems and opportunities.
    """
)


# =========================================================
# USER INPUT
# =========================================================

MAX_PROMPT_LENGTH = 1000
MAX_SESSION_RUNS = 5

if "research_runs" not in st.session_state:
    st.session_state.research_runs = 0

question = st.text_area(
    "Research question",
    placeholder=(
        "Example: Analyze our seller onboarding problem "
        "using our metrics, customer feedback, and "
        "current industry best practices."
    ),
    height=130,
    max_chars=MAX_PROMPT_LENGTH,
    help=f"Maximum {MAX_PROMPT_LENGTH:,} characters."
)

st.caption(
    f"{len(question):,} / {MAX_PROMPT_LENGTH:,} characters"
)

runs_remaining = MAX_SESSION_RUNS - st.session_state.research_runs

st.caption(
    f"Research runs remaining this session: "
    f"{runs_remaining} / {MAX_SESSION_RUNS}"
)
run_button = st.button(
    "Run Research",
    type="primary"
    disabled=runs_remaining <= 0
)

if runs_remaining <= 0:
    st.info(
        "You've reached the 5-run limit for this demo session."
    )
    
# =========================================================
# RUN AGENT
# =========================================================

if run_button:

    if not question.strip():

        st.warning(
            "Enter a research question first."
        )
    elif len(question) > MAX_PROMPT_LENGTH:

        st.error(
            f"Research questions are limited to "
            f"{MAX_PROMPT_LENGTH:,} characters."
        )
    else:
        # Count this as a research run
        st.session_state.research_runs += 1

        try:

            with st.status(
                "ProductScout is researching...",
                expanded=True
            ) as status:

                def handle_agent_event(event):

                    event_type = event["type"]

                    if event_type == "iteration":

                        status.write(
                            f"🧠 Agent iteration "
                            f"{event['iteration']}"
                        )

                    elif event_type == "tool_start":

                        tool = event["tool"]

                        if tool == "get_marketplace_data":

                            status.write(
                                "📊 Retrieving internal "
                                "marketplace metrics..."
                            )

                        elif tool == "get_customer_feedback":

                            status.write(
                                "💬 Reviewing customer "
                                "feedback..."
                            )

                        elif tool == "search_web":

                            query = event[
                                "arguments"
                            ].get(
                                "query",
                                ""
                            )

                            status.write(
                                "🌐 Searching the web..."
                            )

                            status.caption(
                                query
                            )

                        else:

                            status.write(
                                f"🔧 Running {tool}..."
                            )

                    elif event_type == "tool_complete":

                        tool = event["tool"]

                        if tool == "get_marketplace_data":

                            status.write(
                                "✅ Internal metrics retrieved"
                            )

                        elif tool == "get_customer_feedback":

                            status.write(
                                "✅ Customer feedback analyzed"
                            )

                        elif tool == "search_web":

                            status.write(
                                "✅ Web research completed"
                            )

                    elif event_type == "complete":

                        status.write(
                            "✅ Evidence sufficient"
                        )

                result = run_productscout(
                    question,
                    event_callback=handle_agent_event
                )

                status.update(
                    label="Research complete",
                    state="complete",
                    expanded=False
                )

        except Exception as error:

            st.error(
                "ProductScout encountered an error."
            )

            st.exception(error)

        else:

            # =============================================
            # AGENT ACTIVITY
            # =============================================

            st.subheader(
                "Agent Activity"
            )

            if result["activity"]:

                for activity in result["activity"]:

                    tool_name = activity["tool"]

                    if tool_name == "get_marketplace_data":
                        display_name = (
                            "Internal Marketplace Metrics"
                        )

                    elif tool_name == "get_customer_feedback":
                        display_name = (
                            "Customer Feedback"
                        )

                    elif tool_name == "search_web":
                        display_name = (
                            "Web Research"
                        )

                    else:
                        display_name = tool_name

                    with st.expander(
                        f"✓ Iteration "
                        f"{activity['iteration']}: "
                        f"{display_name}"
                    ):

                        st.write(
                            "Tool:",
                            tool_name
                        )

                        st.write(
                            "Arguments:"
                        )

                        st.code(
                            json.dumps(
                                activity["arguments"],
                                indent=2
                            ),
                            language="json"
                        )

            else:

                st.info(
                    "The agent determined that no "
                    "external tools were required."
                )


            # =============================================
            # EXECUTION METRICS
            # =============================================

            st.subheader(
                "Execution Summary"
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.metric(
                    "Iterations",
                    result["iterations"]
                )

            with col2:

                st.metric(
                    "Tool Calls",
                    result["total_tool_calls"]
                )

            with col3:

                st.metric(
                    "Web Searches",
                    result["web_search_calls"]
                )
            with col4:
                st.metric(
                    "Runtime",
                    f"{result['execution_time']:.1f}s"
                )
                
            col5, col6, col7, col8 = st.columns(4)
            
            with col5:
                st.metric(
                    "Input Tokens",
                    f"{result['input_tokens']:,}"
                )

            with col6:
                st.metric(
                    "Output Tokens",
                    f"{result['output_tokens']:,}"
                )

            with col7:
                st.metric(
                    "Total Tokens",
                    f"{result['total_tokens']:,}"
                )

            with col8:
                st.metric(
                    "Est. LLM Cost",
                    f"${result['estimated_llm_cost']:.4f}"
                )




            # =============================================
            # FINAL ANALYSIS
            # =============================================

            st.divider()

            st.subheader(
                "Product Analysis"
            )

            st.markdown(
                result["answer"]
            )


            # =============================================
            # SOURCES
            # =============================================

            if result["sources"]:

                st.divider()

                st.subheader(
                    "Web Sources"
                )

                for number, url in enumerate(
                    result["sources"],
                    start=1
                ):

                    st.markdown(
                        f"{number}. [{url}]({url})"
                    )

