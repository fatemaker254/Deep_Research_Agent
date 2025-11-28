# models/base.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class LLMInterface(ABC):
    """Abstract LLM wrapper interface."""

    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None,
                 max_tokens: int = 512, temperature: float = 0.0,
                 **kwargs) -> Dict[str, Any]:
        """
        Generate text from the LLM.

        Returns a dict with at least keys: text (str), raw (provider raw response)
        """
        raise NotImplementedError
