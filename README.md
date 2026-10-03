# ProductScout AI

ProductScout is an agentic AI product research assistant that combines internal product metrics, customer feedback, and live web research to investigate product problems and opportunities.

## What It Demonstrates

ProductScout demonstrates several core agentic AI concepts:

- LLM-driven tool selection
- Function calling
- Multi-tool execution
- Iterative agent loops
- External API integration
- Web research
- Agent observability
- Token and cost monitoring
- Maximum-iteration safety controls

## How It Works

A user provides a product research question.

The LLM determines what information it needs and can choose among three tools:

1. Internal marketplace metrics
2. Customer feedback
3. Live web search

The Python orchestration layer executes the requested tools and returns the observations to the LLM.

The LLM then decides whether it has enough evidence to answer or whether another tool call is required.

## Architecture

User  
↓  
Streamlit UI  
↓  
ProductScout Agent  
↓  
LLM decides next action  
↓  
Tools  
- Marketplace Metrics
- Customer Feedback
- Web Search  
↓  
Observations returned to LLM  
↓  
Continue research or produce final analysis

## Technology

- Python
- OpenAI Responses API
- Tavily Search API
- Streamlit

## Running Locally

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate