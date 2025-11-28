# agent/controller.py
from typing import Optional, List, Dict, Any
from models.openai import OpenAIWrapper
from models.base import LLMInterface
from agent.task_decomposition import TaskDecomposer
from agent.synthesizer import Synthesizer
from tools.search import get_search_tool
from tools.base import SearchResult
import logging

logger = logging.getLogger("DeepResearchAgent")
logging.basicConfig(level=logging.INFO)

class DeepResearchAgent:
    def __init__(self, llm: Optional[LLMInterface] = None, search_provider: str = "mock", search_kwargs: dict = None):
        self.llm = llm or OpenAIWrapper()
        self.decomposer = TaskDecomposer(self.llm)
        self.synthesizer = Synthesizer(self.llm)
        self.search_tool = get_search_tool(provider=search_provider, **(search_kwargs or {}))

    def _should_search(self, task_text: str) -> bool:
        # heuristic: if the task contains wh-words or asks for evidence
        t = task_text.lower()
        if any(w in t for w in ["who", "what", "when", "where", "how", "why", "latest", "evidence", "cite", "show"]):
            return True
        # else: search by default for open research
        return True

    def run(self, user_query: str, desired_output_structure: Optional[str] = None,
            results_per_task: int = 5, domain_filters: Optional[List[str]] = None) -> Dict[str, Any]:
        # 1. Decompose
        tasks = self.decomposer.decompose(user_query, desired_output_structure)
        logger.info("Decomposed into %d tasks", len(tasks))
        # 2. For each task, decide whether to invoke search and call search tool
        all_results: Dict[str, List[SearchResult]] = {}
        for t in tasks:
            tid = t["id"]
            text = t["task"]
            if self._should_search(text):
                try:
                    hits = self.search_tool.search(text, n=results_per_task, domain_filters=domain_filters)
                except Exception as e:
                    logger.warning("Search tool error: %s; falling back to mock", e)
                    from tools.search import MockSearch
                    hits = MockSearch().search(text, n=results_per_task)
                all_results[tid] = hits
            else:
                all_results[tid] = []
        # 3. Synthesize final brief
        final = self.synthesizer.synthesize_brief(user_query, tasks, all_results, desired_output_structure)
        return final
