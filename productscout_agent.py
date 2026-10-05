from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv

import json
import os
import time


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

client = OpenAI()

tavily_client = TavilyClient(
    api_key=os.environ["TAVILY_API_KEY"]
)


# =========================================================
# MODEL + PRICING
# =========================================================

MODEL = "gpt-5-mini"
MAX_PROMPT_LENGTH = 1000
INPUT_PRICE_PER_MILLION = 0.25
CACHED_INPUT_PRICE_PER_MILLION = 0.025
OUTPUT_PRICE_PER_MILLION = 2.00


# =========================================================
# INTERNAL DATA HELPERS
# =========================================================

def normalize_seller_topic(topic):
    normalized_topic = topic.lower()

    if (
        "seller" in normalized_topic
        and (
            "onboarding" in normalized_topic
            or "verification" in normalized_topic
            or "identity" in normalized_topic
        )
    ):
        return "seller_onboarding"

    return normalized_topic.replace(" ", "_")


# =========================================================
# TOOLS
# =========================================================

def get_marketplace_data(topic):
    """
    Simulates internal quantitative marketplace data.
    """

    data_key = normalize_seller_topic(topic)

    fake_data = {
        "seller_onboarding": {
            "dropoff_rate": "28%",
            "average_completion_time": "11 minutes",
            "top_issue": "identity verification friction"
        }
    }

    return fake_data.get(
        data_key,
        {
            "message":
            "No marketplace data found for that topic."
        }
    )


def get_customer_feedback(topic):
    """
    Simulates qualitative customer feedback.
    """

    data_key = normalize_seller_topic(topic)

    fake_feedback = {
        "seller_onboarding": [
            "I had to upload my ID three times.",
            "I wasn't sure why my identity verification failed.",
            "The process took too long.",
            "I didn't know how many steps were left."
        ]
    }

    return fake_feedback.get(
        data_key,
        ["No customer feedback found for that topic."]
    )


def search_web(query):
    """
    Searches the live web using Tavily.
    """

    results = tavily_client.search(
        query,
        max_results=5
    )

    simplified_results = []

    for result in results["results"]:
        simplified_results.append(
            {
                "title": result["title"],
                "url": result["url"],
                "content": result["content"]
            }
        )

    return simplified_results


# =========================================================
# TOOL DEFINITIONS FOR THE LLM
# =========================================================

tools = [
    {
        "type": "function",
        "name": "get_marketplace_data",
        "description": (
            "Get quantitative internal marketplace metrics "
            "such as drop-off rates, completion times, "
            "and funnel performance."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": (
                        "The marketplace topic to retrieve "
                        "metrics for."
                    )
                }
            },
            "required": ["topic"]
        }
    },
    {
        "type": "function",
        "name": "get_customer_feedback",
        "description": (
            "Get qualitative customer feedback, complaints, "
            "and comments about a marketplace experience."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": (
                        "The marketplace topic to retrieve "
                        "customer feedback for."
                    )
                }
            },
            "required": ["topic"]
        }
    },
    {
        "type": "function",
        "name": "search_web",
        "description": (
            "Search the web for current external information, "
            "industry research, competitors, technologies, "
            "vendors, trends, benchmarks, and examples."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The search query to send to the "
                        "web search engine."
                    )
                }
            },
            "required": ["query"]
        }
    }
]


# =========================================================
# AGENT INSTRUCTIONS
# =========================================================

agent_instructions = """
You are ProductScout, an AI product research assistant.

Your job is to decide what evidence you need before answering.

Available capabilities:

- Use get_marketplace_data for quantitative internal
  marketplace metrics.

- Use get_customer_feedback for qualitative customer
  complaints and feedback.

- Use search_web for current external information,
  industry practices, competitors, vendors,
  technologies, benchmarks, market trends,
  and external examples.

Evidence rules:

- If the user asks about current information, industry
  practices, best practices, competitors, market trends,
  vendors, benchmarks, or external examples,
  you MUST use search_web.

- If the user asks about our marketplace performance,
  use get_marketplace_data.

- If the user asks what our customers are saying,
  experiencing, or complaining about,
  use get_customer_feedback.

- If a question requires multiple types of evidence,
  use multiple tools.

- If a question combines internal performance,
  customer feedback, and external industry practices,
  use ALL THREE tools.

- Do not use a tool for simple definitions or
  conceptual explanations when no evidence is required.

Research behavior:

- Examine tool results before deciding what to do next.

- If the evidence is insufficient or incomplete,
  call another appropriate tool or refine your search.

- You may call the same tool more than once with
  different arguments.

- Do not repeat identical searches unnecessarily.

- Stop using tools once you have enough evidence
  to answer the user's question.

Answer behavior:

- Base factual conclusions on evidence returned by tools.

- Clearly distinguish retrieved evidence from
  your own analysis.

- When using web search results, include relevant
  source URLs in the final answer.
"""


# =========================================================
# MAIN AGENT FUNCTION
# =========================================================

def run_productscout(question, event_callback=None):

    if not isinstance(question, str):
        raise ValueError(
            "Question must be a text string."
        )

    question = question.strip()

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )

    if len(question) > MAX_PROMPT_LENGTH:
        raise ValueError(
            f"Question exceeds the "
            f"{MAX_PROMPT_LENGTH:,}-character limit."
        )
    # -----------------------------------------------------
    # UI / OBSERVABILITY EVENT HELPER
    # -----------------------------------------------------

    def emit(event_type, **data):
        if event_callback:
            event_callback(
                {
                    "type": event_type,
                    **data
                }
            )

    # -----------------------------------------------------
    # TOKEN COUNTERS
    # -----------------------------------------------------

    total_input_tokens = 0
    total_cached_tokens = 0
    total_output_tokens = 0

    def add_usage(response):
        nonlocal total_input_tokens
        nonlocal total_cached_tokens
        nonlocal total_output_tokens

        if response.usage is None:
            return

        total_input_tokens += (
            response.usage.input_tokens
        )

        total_output_tokens += (
            response.usage.output_tokens
        )

        input_details = (
            response.usage.input_tokens_details
        )

        if input_details:
            total_cached_tokens += (
                input_details.cached_tokens or 0
            )

    # -----------------------------------------------------
    # COST HELPER
    # -----------------------------------------------------

    def calculate_cost():
        uncached_input_tokens = max(
            total_input_tokens - total_cached_tokens,
            0
        )

        input_cost = (
            uncached_input_tokens
            / 1_000_000
            * INPUT_PRICE_PER_MILLION
        )

        cached_input_cost = (
            total_cached_tokens
            / 1_000_000
            * CACHED_INPUT_PRICE_PER_MILLION
        )

        output_cost = (
            total_output_tokens
            / 1_000_000
            * OUTPUT_PRICE_PER_MILLION
        )

        return (
            input_cost
            + cached_input_cost
            + output_cost
        )

    # -----------------------------------------------------
    # RESULT HELPER
    # -----------------------------------------------------

    def build_result(
        answer,
        completed,
        start_time,
        iteration,
        total_tool_calls,
        web_search_calls,
        activity,
        sources
    ):
        elapsed_time = time.time() - start_time

        return {
            "answer": answer,
            "iterations": iteration,
            "total_tool_calls": total_tool_calls,
            "web_search_calls": web_search_calls,
            "execution_time": elapsed_time,
            "input_tokens": total_input_tokens,
            "cached_tokens": total_cached_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": (
                total_input_tokens
                + total_output_tokens
            ),
            "estimated_llm_cost": calculate_cost(),
            "activity": activity,
            "sources": list(
                dict.fromkeys(sources)
            ),
            "completed": completed
        }

    # -----------------------------------------------------
    # RUN STATE
    # -----------------------------------------------------

    start_time = time.time()

    total_tool_calls = 0
    web_search_calls = 0
    iteration = 0

    MAX_ITERATIONS = 5

    activity = []
    sources = []

    # =====================================================
    # INITIAL LLM REQUEST
    # =====================================================

    response = client.responses.create(
        model=MODEL,
        instructions=agent_instructions,
        input=question,
        tools=tools,
        tool_choice="auto"
    )

    add_usage(response)

    # =====================================================
    # AGENT LOOP
    # =====================================================

    while iteration < MAX_ITERATIONS:

        iteration += 1

        emit(
            "iteration",
            iteration=iteration
        )

        function_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        # -------------------------------------------------
        # NO TOOL CALLS = AGENT IS DONE
        # -------------------------------------------------

        if not function_calls:

            emit(
                "complete",
                iteration=iteration
            )

            return build_result(
                answer=response.output_text,
                completed=True,
                start_time=start_time,
                iteration=iteration,
                total_tool_calls=total_tool_calls,
                web_search_calls=web_search_calls,
                activity=activity,
                sources=sources
            )

        # -------------------------------------------------
        # EXECUTE EVERY REQUESTED TOOL
        # -------------------------------------------------

        tool_outputs = []

        for item in function_calls:

            total_tool_calls += 1

            arguments = json.loads(
                item.arguments
            )

            emit(
                "tool_start",
                iteration=iteration,
                tool=item.name,
                arguments=arguments
            )

            activity.append(
                {
                    "iteration": iteration,
                    "tool": item.name,
                    "arguments": arguments
                }
            )

            if item.name == "get_marketplace_data":

                tool_result = get_marketplace_data(
                    arguments["topic"]
                )

            elif item.name == "get_customer_feedback":

                tool_result = get_customer_feedback(
                    arguments["topic"]
                )

            elif item.name == "search_web":

                web_search_calls += 1

                tool_result = search_web(
                    arguments["query"]
                )

                for result in tool_result:
                    if result.get("url"):
                        sources.append(
                            result["url"]
                        )

            else:

                tool_result = {
                    "error":
                    f"Unknown tool: {item.name}"
                }

            emit(
                "tool_complete",
                iteration=iteration,
                tool=item.name
            )

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(
                        tool_result
                    )
                }
            )

        # -------------------------------------------------
        # RETURN ALL OBSERVATIONS TO THE MODEL
        # -------------------------------------------------

        response = client.responses.create(
            model=MODEL,
            instructions=agent_instructions,
            previous_response_id=response.id,
            input=tool_outputs,
            tools=tools,
            tool_choice="auto"
        )

        add_usage(response)

    # =====================================================
    # MAXIMUM ITERATIONS REACHED
    # =====================================================

    emit(
        "stopped",
        iteration=iteration
    )

    return build_result(
        answer=(
            "ProductScout reached the maximum number "
            "of research iterations before completing."
        ),
        completed=False,
        start_time=start_time,
        iteration=iteration,
        total_tool_calls=total_tool_calls,
        web_search_calls=web_search_calls,
        activity=activity,
        sources=sources
    )
