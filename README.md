# 🔍 Deep Research Agent GenAI Task

A modular, production-aligned **Deep Research Agent** capable of autonomous research, multi-step reasoning, and citation-aware synthesis.

- Multi-step reasoning & task orchestration  
- Tool-augmented research workflows  
- Proper separation of concerns  
- Testable Python architecture  
- JSON-based structured output

> This is **not a chatbot** — it is an autonomous research system designed to break down complex questions, retrieve information, and synthesize reliable insights.

## Core Capabilities

- Accepts open-ended research prompts
- Decomposes questions into structured subtasks
- Identifies subtasks that require external information
- Invokes a search tool for retrieval when needed
- Normalizes and scores retrieved sources (relevance, recency, reliability)
- Deduplicates overlapping information and extracts key facts
- Generates a final concise research brief with **proper citations**
- Tracks contradictions and uncertainties in data

## Sample Output
INFO:DeepResearchAgent:Decomposed into 1 tasks
{
  "sections": [
    {
      "order": 1,
      "content": "[MOCK LLM] Would respond to: Summarize the main findings for the sub-question: \"What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults\". Use the following sources:\n1. Mock result 3 for 'What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults' - https://research.example/article/3/e67b0fa2\nProvide 3 concise bullets and mention any"
    }
  ],
  "conclusion": "[MOCK LLM] Would respond to: Using the above task-level summaries, produce a concise research brief for the research question: \"What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults?\". Include: short conclusion (2-3 sentences), contradictions/uncertainties list, and short recommendations if any. Also output a JSON object with sections as provided by the agent. Do not invent c",
  "contradictions_and_uncertainities": [],
  "citations": [
    {
      "id": 1,
      "url": "https://example.com/article/1/9efe98cb",
      "title": "Mock result 1 for 'What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults'",
      "domain": "example.com"
    },
    {
      "id": 2,
      "url": "https://example.org/article/2/def90afa",
      "title": "Mock result 2 for 'What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults'",
      "domain": "example.org"
    },
    {
      "id": 3,
      "url": "https://research.example/article/3/e67b0fa2",
      "title": "Mock result 3 for 'What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults'",
      "domain": "research.example"
    },
    {
      "id": 4,
      "url": "https://example.com/article/4/177af415",
      "title": "Mock result 4 for 'What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults'",
      "domain": "example.com"
    },
    {
      "id": 4,
      "url": "https://example.com/article/4/177af415",
      "title": "Mock result 4 for 'What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults'",
      "domain": "example.com"
    {
      "id": 4,
      "url": "https://example.com/article/4/177af415",
      "title": "Mock result 4 for 'What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults'",
    {
      "id": 4,
      "url": "https://example.com/article/4/177af415",
    {
      "id": 4,
    {
    {
    {
      "id": 4,
      "url": "https://example.com/article/4/177af415",
      "title": "Mock result 4 for 'What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults'",
      "domain": "example.com"
    },
    {
      "id": 5,
      "url": "https://example.org/article/5/274e5158",
      "title": "Mock result 5 for 'What are the latest peer-reviewed findings about the cognitive effects of intermittent fasting in adults'",
      "domain": "example.org"
    }
  ]
}
