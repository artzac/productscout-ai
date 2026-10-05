from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv

import json
import os
import time
import requests

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

# =========================================================
# SYNTHETIC INTERNAL IDENTITY + RISK DATA
# =========================================================

SUPPORTED_TOPICS = [
    "registration_friction",
    "contact_verification",
    "document_verification",
    "biometric_liveness",
    "fraudulent_accounts",
    "false_positive_risk",
    "bot_signup_abuse",
    "account_takeover",
    "account_recovery",
    "international_identity"
]


# Natural-language phrases that map to canonical topic keys.
# More specific topics are intentionally listed before
# broader topics such as registration_friction.

TOPIC_ALIASES = {
    "account_takeover": [
        "account takeover",
        "ato",
        "compromised account",
        "credential stuffing",
        "stolen credentials",
        "suspicious login",
        "unauthorized login",
        "login risk"
    ],

    "account_recovery": [
        "account recovery",
        "recover account",
        "forgot password",
        "password recovery",
        "reset password",
        "lost phone",
        "old phone number",
        "old email",
        "locked out"
    ],

    "international_identity": [
        "international identity",
        "international verification",
        "international registration",
        "international users",
        "global identity",
        "foreign document",
        "foreign id",
        "non us",
        "non-us",
        "transliteration",
        "two last names",
        "latin america"
    ],

    "bot_signup_abuse": [
        "bot signup",
        "bot registration",
        "bots",
        "automated signup",
        "automated registration",
        "captcha",
        "scripted signup",
        "scripted registration"
    ],

    "false_positive_risk": [
        "false positive",
        "false positives",
        "legitimate users blocked",
        "legitimate user blocked",
        "risk review",
        "manual review",
        "risk decision",
        "risk suspension",
        "suspended after registration",
        "appeal",
        "appeals"
    ],

    "fraudulent_accounts": [
        "fraudulent account",
        "fraudulent accounts",
        "fraud registration",
        "synthetic identity",
        "synthetic identities",
        "duplicate account",
        "duplicate accounts",
        "multiple accounts",
        "multi account",
        "multi-account",
        "device linked to multiple identities",
        "identity fraud"
    ],

    "biometric_liveness": [
        "biometric",
        "biometrics",
        "liveness",
        "selfie",
        "face match",
        "facial verification",
        "face verification"
    ],

    "document_verification": [
        "document verification",
        "identity document",
        "id document",
        "id upload",
        "driver's license",
        "drivers license",
        "passport",
        "document upload",
        "identity verification"
    ],

    "contact_verification": [
        "contact verification",
        "phone verification",
        "email verification",
        "sms verification",
        "sms",
        "otp",
        "one time password",
        "one-time password",
        "verification code"
    ],

    "registration_friction": [
        "registration friction",
        "registration",
        "signup",
        "sign up",
        "sign-up",
        "account creation",
        "onboarding",
        "seller onboarding",
        "registration funnel",
        "registration conversion",
        "registration abandonment",
        "signup abandonment"
    ]
}


INTERNAL_METRICS = {

    "registration_friction": {
        "registration_completion_rate": "72%",
        "overall_dropoff_rate": "28%",
        "median_completion_time": "8.7 minutes",
        "mobile_completion_rate": "66%",
        "desktop_completion_rate": "79%",
        "highest_dropoff_step": "identity verification",
        "dropoff_at_identity_step": "13.6%"
    },

    "contact_verification": {
        "otp_first_attempt_success_rate": "84%",
        "otp_resend_rate": "19%",
        "otp_delivery_failure_rate": "5.8%",
        "median_verification_time": "74 seconds",
        "verification_abandonment_rate": "7.2%",
        "support_contact_rate": "3.9%",
        "highest_failure_channel": "SMS"
    },

    "document_verification": {
        "first_attempt_pass_rate": "71%",
        "retry_rate": "20%",
        "hard_failure_rate": "9%",
        "median_verification_time": "4.8 minutes",
        "average_upload_attempts": "1.7",
        "top_failure_reason": "blurry image or glare",
        "image_quality_related_failures": "37%"
    },

    "biometric_liveness": {
        "first_attempt_pass_rate": "82%",
        "retry_rate": "12%",
        "failure_rate": "6%",
        "average_attempts": "1.4",
        "failure_rate_on_older_mobile_devices": "10.4%",
        "top_failure_reason": "lighting or face positioning",
        "lighting_or_position_related_failures": "41%"
    },

    "fraudulent_accounts": {
        "registrations_flagged_for_fraud_risk": "5.2%",
        "registrations_linked_to_existing_device": "2.8%",
        "suspected_synthetic_identity_rate": "0.9%",
        "confirmed_duplicate_account_rate": "1.6%",
        "high_risk_accounts_blocked_before_activation": "68%",
        "top_risk_signal": "device linked to multiple identities"
    },

    "false_positive_risk": {
        "registrations_sent_to_risk_review": "8.4%",
        "reviewed_users_eventually_approved": "64%",
        "median_manual_review_time": "11.2 hours",
        "users_abandoning_during_review": "14%",
        "risk_related_support_contact_rate": "18%",
        "appeal_success_rate": "57%"
    },

    "bot_signup_abuse": {
        "estimated_automated_registration_attempts": "3.7%",
        "bot_attempts_blocked": "91%",
        "registrations_receiving_captcha": "12%",
        "captcha_abandonment_rate": "6.2%",
        "legitimate_users_incorrectly_challenged": "2.1%",
        "top_bot_signal": (
            "high velocity registration from shared infrastructure"
        )
    },

    "account_takeover": {
        "logins_flagged_as_high_risk": "2.6%",
        "logins_receiving_step_up_authentication": "8.9%",
        "confirmed_account_takeover_rate": "0.21%",
        "suspected_takeovers_blocked": "94%",
        "median_customer_recovery_time": "18 hours",
        "top_attack_vector": "compromised credentials"
    },

    "account_recovery": {
        "self_service_recovery_success_rate": "76%",
        "recovery_abandonment_rate": "17%",
        "support_escalation_rate": "24%",
        "median_self_service_recovery_time": "12.6 minutes",
        "users_making_multiple_recovery_attempts": "15%",
        "top_failure_reason": (
            "no access to registered phone or email"
        )
    },

    "international_identity": {
        "us_first_attempt_verification_rate": "78%",
        "international_first_attempt_verification_rate": "63%",
        "international_manual_review_rate": "26%",
        "unsupported_document_rate": "8.6%",
        "name_transliteration_mismatch_rate": "6.9%",
        "median_international_verification_time": "18.5 minutes",
        "highest_friction_region": "Latin America"
    }
}


CUSTOMER_FEEDBACK = {

    "registration_friction": [
        "I didn't realize registration would take this long.",
        "I thought I was almost finished and then it asked me "
        "for more information.",
        "The process is much harder on my phone.",
        "I wasn't sure how many steps were left.",
        "I gave up because I didn't have all the information "
        "it was asking for."
    ],

    "contact_verification": [
        "The verification code never arrived.",
        "By the time I received the code it had expired.",
        "I requested another code and then both codes arrived.",
        "I entered the code correctly but it told me it was invalid.",
        "I don't have access to my old phone number anymore."
    ],

    "document_verification": [
        "I had to upload my driver's license three times.",
        "The picture looked perfectly clear to me but it kept "
        "rejecting it.",
        "It didn't explain what was wrong with my ID.",
        "The camera had trouble focusing on my license.",
        "I wasn't sure whether it wanted the front, back, "
        "or both sides."
    ],

    "biometric_liveness": [
        "It kept telling me to move closer and then farther away.",
        "The selfie verification would not recognize me.",
        "I wear glasses and wasn't sure if I was supposed "
        "to remove them.",
        "It worked after I moved to a room with better lighting.",
        "I don't understand why you need a picture of my face."
    ],

    "fraudulent_accounts": [
        "My wife and I share the same tablet. Why was my "
        "account blocked?",
        "It says I already have an account but I don't remember "
        "creating one.",
        "I moved recently and now it won't let me register.",
        "I was told my information was associated with "
        "another account.",
        "I don't understand why my registration was considered "
        "suspicious."
    ],

    "false_positive_risk": [
        "I have no idea why my account was suspended immediately "
        "after registration.",
        "I provided everything you asked for and I'm still waiting.",
        "Nobody told me what information I need to provide "
        "to fix this.",
        "I appealed the decision but don't know when someone "
        "will review it.",
        "I'm a legitimate customer and feel like I'm being "
        "treated like a fraudster."
    ],

    "bot_signup_abuse": [
        "Why do I have to prove I'm human twice?",
        "The CAPTCHA keeps failing on my phone.",
        "I completed the CAPTCHA but it sent me back to "
        "the same screen.",
        "The image challenge was difficult to see.",
        "I don't understand why I'm being treated like a bot."
    ],

    "account_takeover": [
        "I received a password reset email that I didn't request.",
        "Someone changed the email address on my account.",
        "I suddenly couldn't log in using my password.",
        "I received a verification code even though I wasn't "
        "trying to sign in.",
        "I reported that my account was compromised but recovery "
        "took too long."
    ],

    "account_recovery": [
        "I changed phone numbers and now I can't access my account.",
        "The recovery code is being sent to an email address "
        "I no longer use.",
        "I keep getting sent in circles between login and "
        "account recovery.",
        "I can prove who I am but there isn't another "
        "verification option.",
        "I finally contacted support because self-service "
        "recovery didn't work."
    ],

    "international_identity": [
        "My national ID isn't listed as an accepted document.",
        "My name contains two last names but the form only "
        "seems to expect one.",
        "The spelling on my passport is different from the "
        "spelling on my account.",
        "I don't have a US driver's license.",
        "The verification process seems designed only for "
        "US customers."
    ]
}


# =========================================================
# INTERNAL DATA HELPERS
# =========================================================

def normalize_topic(topic):
    """
    Maps natural-language identity and risk topics to one of
    ProductScout's canonical synthetic-data categories.
    """

    normalized = topic.lower().strip()

    # Normalize common separators.
    normalized = normalized.replace("_", " ")
    normalized = normalized.replace("-", " ")
    normalized = " ".join(normalized.split())

    # First check whether the caller supplied an exact
    # canonical topic name.
    canonical_candidate = normalized.replace(" ", "_")

    if canonical_candidate in SUPPORTED_TOPICS:
        return canonical_candidate

    # Then look for natural-language aliases.
    for topic_key, aliases in TOPIC_ALIASES.items():
        for alias in aliases:
            normalized_alias = alias.replace("-", " ")

            if normalized_alias in normalized:
                return topic_key

    # Preserve the unknown topic so the tool can explain
    # that no matching synthetic dataset exists.
    return canonical_candidate


# =========================================================
# TOOLS
# =========================================================

def get_marketplace_data(topic):
    """
    Returns synthetic internal quantitative identity,
    registration, and risk metrics for the demo.
    """

    data_key = normalize_topic(topic)

    if data_key not in INTERNAL_METRICS:
        return {
            "data_source": "synthetic_demo_data",
            "message": (
                f"No internal demo metrics found for topic: {topic}"
            ),
            "supported_topics": SUPPORTED_TOPICS
        }

    return {
        "data_source": "synthetic_demo_data",
        "topic": data_key,
        "metrics": INTERNAL_METRICS[data_key]
    }


def get_customer_feedback(topic):
    """
    Returns synthetic qualitative customer feedback
    for identity, registration, and risk experiences.
    """

    data_key = normalize_topic(topic)

    if data_key not in CUSTOMER_FEEDBACK:
        return {
            "data_source": "synthetic_demo_data",
            "message": (
                f"No customer feedback found for topic: {topic}"
            ),
            "supported_topics": SUPPORTED_TOPICS
        }

    return {
        "data_source": "synthetic_demo_data",
        "topic": data_key,
        "feedback": CUSTOMER_FEEDBACK[data_key]
    }

def search_web(query):
    """
    Searches the live web using Tavily.
    Retries temporary connection failures before giving up.
    """

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):

        try:
            results = tavily_client.search(
                query,
                max_results=5,
                timeout=20
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

        except requests.exceptions.RequestException as error:

            if attempt < max_attempts:
                time.sleep(2 ** (attempt - 1))
                continue

            return [
                {
                    "title": "Web search temporarily unavailable",
                    "url": "",
                    "content": (
                        "Live web search could not be completed "
                        "because of a temporary connection problem. "
                        "Continue the analysis using available internal "
                        "data and customer feedback, and clearly state "
                        "that live web research was unavailable."
                    )
                }
            ]


# =========================================================
# TOOL DEFINITIONS FOR THE LLM
# =========================================================

tools = [
    {
        "type": "function",
        "name": "get_marketplace_data",
        "description": (
            "Get synthetic internal quantitative metrics for "
            "registration, identity, authentication, and risk. "
            "Available areas include registration friction, "
            "contact verification, document verification, "
            "biometric/liveness verification, fraudulent accounts, "
            "false-positive risk decisions, bot signup abuse, "
            "account takeover, account recovery, and international "
            "identity verification."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": (
                        "The registration, identity, authentication, or risk "
                        "problem to retrieve internal metrcis for. Natural"
                        "language is accepted."
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
        "Get synthetic qualitative customer feedback and "
        "complaints about registration, identity verification, "
        "authentication, account security, and risk experiences."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": (
                    "The registration, identity, authentication, or risk "
                    "problem to retrieve customer feedback for. Natural "
                    "language is accepted."
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

- Use get_marketplace_data for synthetic quantitative
  internal metrics covering registration, identity,
  authentication, account security, and risk.

- Use get_customer_feedback for synthetic qualitative
  customer complaints and feedback covering registration,
  identity, authentication, account security, and risk.

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
- Internal metrics and customer feedback are synthetic
  demo data. Never imply that these numbers or comments
  belong to a real company.

- The internal dataset contains multiple problem areas.
  Do not assume registration represents all identity or
  risk issues.

- For broad questions spanning several problem areas,
  you may call get_marketplace_data or
  get_customer_feedback multiple times with different
  topics.

- If an internal-data tool reports that no dataset exists
  for the requested topic, inspect its supported_topics
  list and retry with the closest relevant topic when
  appropriate.

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
            "iterations": len(
                {
                    item["iteration"]
                    for item in activity
                    }
                ),
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
