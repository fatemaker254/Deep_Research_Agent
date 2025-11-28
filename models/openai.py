# models/openai.py
import os
from typing import Dict, Any, Optional
from .base import LLMInterface

try:
    import openai
except Exception:
    openai = None

class OpenAIWrapper(LLMInterface):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", default_system: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.default_system = default_system or "You are a helpful research assistant."
        if openai and self.api_key:
            openai.api_key = self.api_key

    def generate(self, prompt: str, system: Optional[str] = None,
                 max_tokens: int = 512, temperature: float = 0.0, **kwargs) -> Dict[str, Any]:
        system_msg = system or self.default_system
        if openai and self.api_key:
            # Using Chat Completions API pattern — adapt to whichever official API your org uses.
            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            text = resp["choices"][0]["message"]["content"].strip()
            return {"text": text, "raw": resp}
        else:
            # Mock fallback for development/testing
            # Provide deterministic mock behavior (simple echo + instruction)
            text = f"[MOCK LLM] Would respond to: {prompt[:400]}"
            return {"text": text, "raw": {"mock": True}}
