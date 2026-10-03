import os
from tavily import TavilyClient

client = TavilyClient(
    api_key=os.environ["TAVILY_API_KEY"]
)

results = client.search(
    "How is AI being used in marketplace seller onboarding?"
)

print(results)