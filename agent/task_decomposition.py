# agent/task_decomposition.py
from typing import List, Dict
from models.base import LLMInterface

# A small, testable task decomposition module.
class TaskDecomposer:
    def __init__(self, llm: LLMInterface):
        self.llm = llm

    def decompose(self, query: str, desired_output_structure: str = None) -> List[Dict]:
        """
        Returns a list of subtasks. Each subtask is a dict:
          {"id": "...", "task": "...", "requires_search": True/False}
        Uses the LLM if available; falls back to heuristic decomposition.
        """
        prompt = (
            "Break the following open research question into 4-8 focused sub-questions "
            "suitable for web research. Output JSON array of objects with 'id' and 'task'.\n\n"
            f"Research question: {query}\n"
        )
        if desired_output_structure:
            prompt += f"\nDesired final structure: {desired_output_structure}\n"
        resp = self.llm.generate(prompt, max_tokens=400, temperature=0.0)
        text = resp.get("text", "")
        # Try to parse the LLM's JSON. If LLM mock or fails, fallback to heuristics.
        import json
        try:
            parsed = json.loads(text)
            # ensure list of dicts with 'task' key
            tasks = []
            for i, item in enumerate(parsed):
                t = str(item.get("task") if isinstance(item, dict) else item)
                tasks.append({"id": f"t{i+1}", "task": t, "requires_search": True})
            if tasks:
                return tasks
        except Exception:
            # Heuristic fallback: split into sentences / clauses
            parts = [p.strip() for p in query.replace("?", ".").split(".") if p.strip()]
            tasks = []
            for i, p in enumerate(parts[:6]):
                tasks.append({"id": f"t{i+1}", "task": p, "requires_search": True})
            if not tasks:
                tasks = [{"id": "t1", "task": query, "requires_search": True}]
            return tasks
        return tasks
