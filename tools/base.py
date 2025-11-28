# tools/base.py
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class SearchResult:
    """Normalized search result used inside the agent."""
    id: str
    title: str
    snippet: str
    url: str
    domain: str
    published_at: Optional[str] = None  # ISO string if available
    score: Optional[float] = None  # internal combined score
    source_rank: Optional[int] = None
    raw: Optional[Dict[str, Any]] = None
