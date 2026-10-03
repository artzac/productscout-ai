from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv

import json
import os
import time


# =========================================================
# ENVIRONMENT SETUP
# =========================================================

load_dotenv()

client = OpenAI()

tavily_client = TavilyClient(
    api_key=os.environ["TAVILY_API_KEY"]
)


# =========================================================
# TOOL FUNCTIONS
# =========================================================

def get_marketplace_data(topic):
    """
    Simulates internal quantitative marketplace data.
    """

    print(
        f"\n[PYTHON TOOL RUNNING] "
        f"get_marketplace_data({topic})"
    )

    normalized_topic = topic.lower()

    if (
        "seller" in normalized_topic
        and (
            "onboarding" in normalized_topic
            or "verification" in normalized_topic
            or "identity" in normalized_topic
        )
    ):
        data_key = "seller_onboarding"
    else:
        data_key = normalized_topic.replace(" ", "_")

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

    print(
        f"\n[PYTHON TOOL RUNNING] "
        f"get_customer_feedback({topic})"
    )

    normalized_topic = topic.lower()

    if (
        "seller" in normalized_topic
        and (
            "onboarding" in normalized_topic
            or "verification" in normalized_topic
            or "identity" in normalized_topic
        )
    ):
        data_key = "seller_onboarding"
    else:
        data_key = normalized_topic.replace(" ", "_")

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

    print(
        f"\n[PYTHON TOOL RUNNING] "
        f"search_web({query})"
    )

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
# TOOL DEFINITIONS EXPOSED TO THE LLM
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
# AGENT POLICY / INSTRUCTIONS
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
# USER INPUT
# =========================================================

user_question = input(
    "\nAsk ProductScout a question: "
)


# =========================================================
# EXECUTION METRICS
# =========================================================

start_time = time.time()

total_tool_calls = 0
web_search_calls = 0

MAX_ITERATIONS = 5
iteration = 0
completed = False


# =========================================================
# INITIAL LLM REQUEST
# =========================================================

response = client.responses.create(
    model="gpt-5-mini",
    instructions=agent_instructions,
    input=user_question,
    tools=tools,
    tool_choice="auto"
)


# =========================================================
# AGENT LOOP
# =========================================================

while iteration < MAX_ITERATIONS:

    iteration += 1

    print(
        f"\n========== AGENT ITERATION "
        f"{iteration} =========="
    )

    # Find all function calls requested by the model
    function_calls = [
        item
        for item in response.output
        if item.type == "function_call"
    ]

    # -----------------------------------------------------
    # No function calls means the model is finished
    # -----------------------------------------------------

    if not function_calls:

        print("\n[AGENT DECISION]")
        print("No more tools needed.")

        print("\n[FINAL ANSWER]")
        print(response.output_text)

        completed = True
        break

    # -----------------------------------------------------
    # Execute every tool requested in this iteration
    # -----------------------------------------------------

    tool_outputs = []

    for item in function_calls:

        total_tool_calls += 1

        print("\n[LLM REQUESTED A TOOL]")
        print("Tool:", item.name)
        print("Arguments:", item.arguments)

        arguments = json.loads(
            item.arguments
        )

        # -----------------------------------------------
        # Route the requested tool call
        # -----------------------------------------------

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

        else:

            tool_result = {
                "error":
                f"Unknown tool: {item.name}"
            }

        print("\n[TOOL RESULT]")
        print(tool_result)

        # -----------------------------------------------
        # Save this tool's result for the LLM
        # -----------------------------------------------

        tool_outputs.append(
            {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(
                    tool_result
                )
            }
        )

    # -----------------------------------------------------
    # Return ALL tool observations to the model
    # -----------------------------------------------------

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=agent_instructions,
        previous_response_id=response.id,
        input=tool_outputs,
        tools=tools,
        tool_choice="auto"
    )


# =========================================================
# SAFETY STOP
# =========================================================

if not completed:

    print("\n[STOPPED]")
    print(
        "Maximum agent iterations reached."
    )


# =========================================================
# EXECUTION SUMMARY
# =========================================================

elapsed_time = time.time() - start_time

print(
    "\n========== EXECUTION SUMMARY =========="
)

print(
    "Agent iterations:",
    iteration
)

print(
    "Total tool calls:",
    total_tool_calls
)

print(
    "Web searches:",
    web_search_calls
)

print(
    f"Execution time: "
    f"{elapsed_time:.2f} seconds"
)