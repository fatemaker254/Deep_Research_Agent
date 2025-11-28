# example_run.py
import os
from agent.controller import DeepResearchAgent
from models.openai import OpenAIWrapper

def main():
    # Configure environment keys as needed; for a demo we use MOCK search and MOCK LLM if no api key
    llm = OpenAIWrapper(api_key=os.environ.get("OPENAI_API_KEY"))
    agent = DeepResearchAgent(llm=llm, search_provider="mock")

    query = "What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults?"
    result = agent.run(query, desired_output_structure="Section per sub-question, conclusion, contradictions, citations")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
