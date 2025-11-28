# tools/search.py
import os
import time
import hashlib
from typing import List, Dict, Optional
from .base import SearchResult
import requests
from dateutil import parser as dateparser  # lightweight and robust

class SearchToolInterface:
    def search(self, query: str, n: int = 5, domain_filters: Optional[List[str]] = None) -> List[SearchResult]:
        raise NotImplementedError

# Helper to generate deterministic id
def _make_id(url: str, title: str) -> str:
    return hashlib.sha1((url + title).encode("utf-8")).hexdigest()

class MockSearch(SearchToolInterface):
    """Deterministic mock search for testing and offline runs."""
    def search(self, query: str, n: int = 5, domain_filters: Optional[List[str]] = None):
        results = []
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        base_domains = ["example.com", "example.org", "research.example"]
        for i in range(min(n, 10)):
            domain = base_domains[i % len(base_domains)]
            title = f"Mock result {i+1} for '{query}'"
            url = f"https://{domain}/article/{i+1}/{hashlib.md5(title.encode()).hexdigest()[:8]}"
            snippet = f"This is a mock snippet for query '{query}'. Contains key tokens: {query.split()[0]}"
            results.append(SearchResult(
                id=_make_id(url, title),
                title=title,
                snippet=snippet,
                url=url,
                domain=domain,
                published_at=now,
                source_rank=i+1,
                raw={"mock_rank": i+1}
            ))
        return results

class GoogleCSE(SearchToolInterface):
    """
    Google Custom Search Engine wrapper. Requires:
      - GOOGLE_CSE_API_KEY (or env GOOGLE_CSE_API_KEY)
      - GOOGLE_CSE_CX (or env GOOGLE_CSE_CX)
    """
    def __init__(self, api_key: Optional[str] = None, cx: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GOOGLE_CSE_API_KEY")
        self.cx = cx or os.environ.get("GOOGLE_CSE_CX")
        self.endpoint = "https://www.googleapis.com/customsearch/v1"

    def search(self, query: str, n: int = 5, domain_filters: Optional[List[str]] = None):
        if not self.api_key or not self.cx:
            raise RuntimeError("Google CSE requires GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX env variables")
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": min(n, 10)
        }
        if domain_filters:
            # Google CSE supports "site:" in query as filter
            params["q"] = " ".join([f"site:{d}" for d in domain_filters]) + " " + query
        resp = requests.get(self.endpoint, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        results = []
        for i, it in enumerate(items[:n]):
            title = it.get("title", "")
            snippet = it.get("snippet", "")
            url = it.get("link", "")
            domain = url.split("/")[2] if url.startswith("http") else ""
            published = None
            # try to find published date in pagemap (not always present)
            results.append(SearchResult(
                id=_make_id(url, title),
                title=title,
                snippet=snippet,
                url=url,
                domain=domain,
                published_at=published,
                source_rank=i+1,
                raw=it
            ))
        return results

class SerperAPI(SearchToolInterface):
    """
    Serper.dev integration (Serper Search).
    Requires SERPER_API_KEY environment variable.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SERPER_API_KEY")
        self.endpoint = "https://api.serper.dev/search"

    def search(self, query: str, n: int = 5, domain_filters: Optional[List[str]] = None):
        if not self.api_key:
            raise RuntimeError("Serper requires SERPER_API_KEY env variable")
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        body = {"q": query, "num": n}
        if domain_filters:
            body["domain"] = domain_filters
        resp = requests.post(self.endpoint, json=body, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        snippets = data.get("organic", [])  # depends on Serper's response format
        results = []
        for i, s in enumerate(snippets[:n]):
            title = s.get("title", "")
            snippet = s.get("snippet", "")
            url = s.get("link", "")
            domain = url.split("/")[2] if url.startswith("http") else ""
            published = s.get("published_at")
            results.append(SearchResult(
                id=_make_id(url, title),
                title=title,
                snippet=snippet,
                url=url,
                domain=domain,
                published_at=published,
                source_rank=i+1,
                raw=s
            ))
        return results

# Factory to pick search provider; returns a SearchToolInterface instance
def get_search_tool(provider: str = "mock", **kwargs) -> SearchToolInterface:
    provider = (provider or "mock").lower()
    if provider == "mock":
        return MockSearch()
    if provider == "google":
        return GoogleCSE(**kwargs)
    if provider == "serper":
        return SerperAPI(**kwargs)
    # Add others (BraveSearch etc.) similarly
    raise ValueError(f"Unknown search provider: {provider}")
