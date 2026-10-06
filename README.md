# ProductScout AI

**Agentic product research for marketplace identity and risk**

ProductScout AI is an agentic research assistant designed for marketplace product teams working on registration, authentication, identity verification, account recovery, fraud, and risk.

It combines **synthetic internal product metrics**, **synthetic customer feedback**, and **live web research** to investigate product problems, evaluate tradeoffs, and recommend areas for further investigation.

### Try it

**Live Demo:** https://prductscout-ai.streamlit.app/  
**Video Walkthrough:** https://www.youtube.com/watch?v=8UqMbBiX-nk

---

## Why I Built It

I built ProductScout as a hands-on project to understand how agentic AI systems work beyond the LLM itself.

The goal was to work directly with the core building blocks of an agentic system:

- Tool definitions
- LLM-driven tool selection
- Structured function calling
- Python orchestration
- Multi-tool execution
- Iterative research loops
- External API integration
- Observability
- Cost tracking
- Failure handling
- Safety and usage controls

The project also gave me a practical way to explore the product decisions behind agentic systems: which capabilities to expose, what evidence the agent should use, when it should continue researching, when it should stop, and how to balance answer quality, latency, cost, and risk.

---

## What ProductScout Does

A user asks ProductScout a product-research question about marketplace identity or risk.

The LLM determines what evidence it needs and can request one or more of three tools:

1. **Internal Product Metrics**  
   Retrieves synthetic quantitative data about registration, authentication, identity, and risk performance.

2. **Customer Feedback**  
   Retrieves synthetic qualitative feedback representing customer complaints and experience.

3. **Live Web Research**  
   Uses the Tavily Search API to retrieve current external information, industry practices, benchmarks, technologies, and examples.

The Python orchestration layer executes the requested tools and returns their observations to the LLM.

The model then decides whether it has enough evidence to answer or whether another research iteration is required.

---

## Example Research Questions

ProductScout includes example prompts covering different identity and risk product problems.

### Authentication & Account Takeover

> Analyze our authentication and account security experience. Use internal metrics and customer feedback to understand where legitimate users are encountering step-up authentication or login friction. Compare our approach with current industry practices and recommend how we should reduce friction without increasing account takeover risk.

### False-Positive Risk

> Legitimate users appear to be getting caught by our risk controls. Analyze our internal metrics and customer feedback, compare them with current industry practices, and recommend how we should reduce false positives without materially increasing fraud.

### International Identity

> Evaluate our international identity-verification experience. Use our internal metrics and customer feedback, research current industry practices, and identify the biggest opportunities.

### Registration Friction

> Analyze friction in our registration experience using internal metrics and customer feedback. Compare our experience with current marketplace best practices and recommend the most important areas to investigate.

Users can also enter their own research questions.

---

## Synthetic Identity & Risk Dataset

ProductScout contains synthetic internal metrics and customer feedback across ten identity and risk problem areas:

- Registration friction
- Email, SMS, and OTP verification
- Identity-document verification
- Biometric and liveness verification
- Fraudulent and duplicate accounts
- False-positive risk decisions
- Bot and automated signup abuse
- Account takeover
- Account recovery
- International identity verification

Natural-language topic mapping allows the agent to translate requests such as:

- "OTP problems"
- "legitimate users getting blocked"
- "CAPTCHA friction"
- "account takeover"
- "international registration"

into the appropriate internal dataset.

> **Important:** All internal metrics and customer feedback in ProductScout are synthetic demo data. They do not represent data from eBay, any previous employer, or any real marketplace.

---

## How the Agent Works

```text
User Research Question
        │
        ▼
   Streamlit UI
        │
        ▼
 ProductScout Agent
        │
        ▼
       LLM
        │
        │ decides what evidence is needed
        ▼
 ┌───────────────────────────────┐
 │          Available Tools      │
 │                               │
 │  📊 Internal Product Metrics  │
 │  💬 Customer Feedback         │
 │  🌐 Live Web Research         │
 └───────────────────────────────┘
        │
        ▼
 Python Orchestration Layer
        │
        │ executes requested tools
        ▼
     Observations
        │
        ▼
       LLM
        │
        ├── Need more evidence?
        │        │
        │       Yes ──► Another tool call
        │
        └── No ──────► Final product analysis
```

The LLM does **not** execute the tools directly.

Instead:

1. The model returns structured function calls.
2. The Python orchestration layer receives those calls.
3. The orchestration layer executes the corresponding functions.
4. Tool results are returned to the model as observations.
5. The model decides whether another research step is necessary.

This observe-decide-act cycle is the core agent loop used by ProductScout.

---

## Agentic AI Concepts Demonstrated

### LLM-Driven Tool Selection

The model determines whether a research question requires internal metrics, customer feedback, web research, or a combination of those sources.

### Multi-Tool Execution

The model can request multiple tools during the same research iteration.

For example, a question comparing internal performance, customer experience, and industry best practices can trigger all three tools.

### Iterative Research

After receiving tool results, the model can determine that additional evidence is required and initiate another research iteration.

### Evidence-Based Synthesis

ProductScout combines retrieved evidence rather than relying only on the model's pretrained knowledge.

### Tool Failure Resilience

Live web research includes retry handling. A temporary external-search failure does not necessarily cause the entire agent to fail.

### Stopping Criteria

The model decides when enough evidence has been gathered to produce a final recommendation, while the orchestration layer enforces a maximum iteration limit.

---

## Observability

Agentic systems can behave differently depending on the question and the evidence returned by tools.

ProductScout therefore exposes execution metrics including:

- Research iterations
- Total tool calls
- Web searches
- Execution time
- Input tokens
- Output tokens
- Total token usage
- Estimated LLM cost

The application also displays agent activity so users can see which tools were selected during each research iteration.

This makes the agent's behavior easier to understand, debug, and evaluate.

---

## Demo Safeguards

Because the public Streamlit application uses live APIs, ProductScout includes several usage controls:

- **1,000-character maximum prompt length**
- **5 research runs per browser session**
- **Maximum agent-iteration limit**
- **Retry handling for temporary web-search failures**
- **API credentials stored outside the source repository using Streamlit secrets**

These controls are designed for a lightweight public demonstration rather than production-grade security or rate limiting.

---

## Technology

- **Python**
- **OpenAI Responses API**
- **GPT-5 mini**
- **Tavily Search API**
- **Streamlit**
- **python-dotenv**
- **Requests**

---

## Project Structure

```text
productscout-ai/
│
├── app.py
│   └── Streamlit user interface and demo controls
│
├── productscout_agent.py
│   └── Agent orchestration, tools, synthetic data,
│       research loop, observability, and cost tracking
│
├── requirements.txt
│
├── .env.example
│
├── .gitignore
│
└── experiments/
    └── Earlier learning and API experiments
```

---

## Running ProductScout Locally

Clone the repository:

```bash
git clone https://github.com/artzac/productscout-ai.git
cd productscout-ai
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```text
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Run the Streamlit application:

```bash
streamlit run app.py
```

The `.env` file is excluded from Git.

---

## Live Demo

Try ProductScout:

https://prductscout-ai.streamlit.app/

The public demo uses synthetic internal data and live web research.

Usage is intentionally limited to control API consumption.

---

## Video Walkthrough

Watch the short ProductScout demo:

https://www.youtube.com/watch?v=8UqMbBiX-nk

The video demonstrates:

- LLM-driven tool selection
- Structured function calling
- Orchestration
- Multi-source research
- The agent loop
- Observability
- Token and cost monitoring

---

## What I Learned

Building ProductScout reinforced an important distinction in agentic AI architecture:

**The LLM reasons about what action to take, but the orchestration layer controls what actions are available and actually performs them.**

The LLM handles semantic reasoning and tool selection.

The surrounding application is responsible for tool implementation, execution, state management, iteration limits, observability, error handling, security, and cost controls.

For product teams, this means designing an agent is not simply a model-selection decision. It requires decisions about capabilities, evidence, autonomy, guardrails, user experience, latency, cost, and failure modes.
