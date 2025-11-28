# agent/synthesizer.py
from typing import List, Dict, Any, Optional
from tools.base import SearchResult
from models.base import LLMInterface
from collections import defaultdict
import math
from datetime import datetime
from dateutil import parser as dateparser

# Simple domain reliability mapping (could be extended or loaded from an external list)
DOMAIN_REPUTATION = {
    "wikipedia.org": 0.7,
    "example.com": 0.5,
    "example.org": 0.55,
    "research.example": 0.8,
}

def _domain_reliability(domain: str) -> float:
    return DOMAIN_REPUTATION.get(domain, 0.5)

def _recency_score(published_at: Optional[str]) -> float:
    if not published_at:
        return 0.5
    try:
        dt = dateparser.parse(published_at)
        days = (datetime.utcnow() - dt).days
        # recency decays with days
        return max(0.0, min(1.0, math.exp(-days/365)))
    except Exception:
        return 0.5

def _text_overlap_score(text_a: str, text_b: str) -> float:
    set_a = set(text_a.lower().split())
    set_b = set(text_b.lower().split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

class Synthesizer:
    def __init__(self, llm: LLMInterface):
        self.llm = llm

    def normalize_and_score(self, results: List[SearchResult], query_keywords: List[str]) -> List[SearchResult]:
        # Normalize published_at to ISO strings where possible (already attempted by search)
        # Score each result for relevance, recency, reliability
        for r in results:
            rel_score = 0.0
            snippet_text = (r.snippet or "") + " " + (r.title or "")
            # relevance: simple keyword overlap
            overlap = sum(1 for k in query_keywords if k.lower() in snippet_text.lower())
            rel_score = overlap / max(1, len(query_keywords))
            recency = _recency_score(r.published_at)
            reliability = _domain_reliability(r.domain)
            # combine scores (weights can be tuned)
            combined = 0.6*rel_score + 0.25*recency + 0.15*reliability
            r.score = round(combined, 4)
        # sort descending by score then by source_rank
        results.sort(key=lambda x: (x.score or 0.0, - (x.source_rank or 9999)), reverse=True)
        return results

    def deduplicate(self, results: List[SearchResult], threshold: float = 0.6) -> List[SearchResult]:
        # Simple deduplication by URL and snippet/title overlap
        kept = []
        seen_urls = set()
        for r in results:
            if r.url in seen_urls:
                continue
            duplicate = False
            for k in kept:
                sim = _text_overlap_score((r.title or "") + " " + (r.snippet or ""), (k.title or "") + " " + (k.snippet or ""))
                if sim > threshold:
                    duplicate = True
                    # keep higher scored one
                    if (r.score or 0) > (k.score or 0):
                        kept.remove(k)
                        seen_urls.discard(k.url)
                    break
            if not duplicate:
                kept.append(r)
                seen_urls.add(r.url)
        return kept

    def extract_facts_vs_opinions(self, results: List[SearchResult]) -> Dict[str, List[Dict[str,str]]]:
        # Use heuristics first; optionally augment with LLM to classify sentences.
        facts = []
        opinions = []
        for r in results:
            text = (r.title or "") + ". " + (r.snippet or "")
            # heuristic: presence of modal verbs, adjectives, "I think", "we believe" -> opinion
            lower = text.lower()
            if any(tok in lower for tok in ["i think", "we think", "perhaps", "may indicate", "suggests", "argue", "opinion"]):
                opinions.append({"url": r.url, "claim": text})
            else:
                # short heuristic: if text has a number/date or 'study' it's probably factual
                if any(ch.isdigit() for ch in text) or "study" in lower:
                    facts.append({"url": r.url, "claim": text})
                else:
                    # fallback to LLM quick classification (if available)
                    prompt = f"Classify the following sentence as FACT or OPINION. Sentence: \"{text}\". Answer FACT or OPINION only."
                    cls = self.llm.generate(prompt, max_tokens=20, temperature=0.0).get("text","")
                    tag = "FACT" if "FACT" in cls.upper() else "OPINION"
                    if tag == "FACT":
                        facts.append({"url": r.url, "claim": text})
                    else:
                        opinions.append({"url": r.url, "claim": text})
        return {"facts": facts, "opinions": opinions}

    def synthesize_brief(self, query: str, tasks: List[Dict], all_results: Dict[str, List[SearchResult]],
                         desired_structure: Optional[str] = None) -> Dict[str, Any]:
        """
        all_results: mapping task_id -> list of SearchResult
        Returns final JSON as specified by the user
        """
        # Aggregate top results across tasks
        aggregated = []
        citations = []
        citation_map = {}
        for tid, reslist in all_results.items():
            for r in reslist[:5]:
                if r.url not in citation_map:
                    cid = len(citation_map) + 1
                    citation_map[r.url] = cid
                    citations.append({"id": cid, "url": r.url, "title": r.title, "domain": r.domain})
                aggregated.append((tid, r))

        # build sections for each task
        sections = []
        contradictions = []
        for idx, task in enumerate(tasks, start=1):
            tid = task["id"]
            reslist = all_results.get(tid, [])[:5]
            # normalize and dedupe
            keywords = [w for w in query.split()[:8]]
            reslist = self.normalize_and_score(reslist, keywords)
            reslist = self.deduplicate(reslist)
            top_points = []
            for r in reslist[:3]:
                cid = citation_map.get(r.url)
                top_points.append(f"{r.title} (cite:{cid}) — {r.snippet[:240]}")
            # quick LLM-based synthesis per task
            task_prompt = (
                f"Summarize the main findings for the sub-question: \"{task['task']}\". "
                f"Use the following sources:\n" + "\n".join([f"{i+1}. {r.title} - {r.url}" for i,r in enumerate(reslist[:5])]) +
                "\nProvide 3 concise bullets and mention any contradictions or uncertainties."
            )
            sresp = self.llm.generate(task_prompt, max_tokens=400, temperature=0.0)
            summary_text = sresp.get("text", "")[:1200]
            sections.append({"order": idx, "content": summary_text})
            # simple detection of "contradiction" keyword
            if "contrad" in summary_text.lower() or "uncertain" in summary_text.lower() or "limitation" in summary_text.lower():
                contradictions.append(f"Task {tid}: possible contradictions or uncertainities noted.")
        # final synthesis across tasks
        final_prompt = (
            f"Using the above task-level summaries, produce a concise research brief for the research question: \"{query}\". "
            f"Include: short conclusion (2-3 sentences), contradictions/uncertainties list, and short recommendations if any. "
            f"Also output a JSON object with sections as provided by the agent. Do not invent citations; reference only by cite:id."
        )
        full_resp = self.llm.generate(final_prompt, max_tokens=500, temperature=0.0)
        conclusion = full_resp.get("text", "").strip()[:800]
        # Build final JSON
        final_json = {
            "sections": sections,
            "conclusion": conclusion,
            "contradictions_and_uncertainities": contradictions,
            "citations": citations
        }
        return final_json
