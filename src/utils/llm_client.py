import json
import math
import requests
from typing import Optional, Dict, Any, Tuple
from src.config import settings

def estimate_tokens(text: str) -> int:
    """Estimates token count (~3.8 characters per token on average for English medical text)."""
    if not text:
        return 0
    return max(1, int(len(text) / 3.8))

def cap_input_tokens(text: str, max_tokens: int) -> Tuple[str, int]:
    """Ensures input prompt stays strictly within the configured input token budget."""
    tokens = estimate_tokens(text)
    if tokens <= max_tokens:
        return text, tokens
    
    # Calculate character budget
    char_limit = int(max_tokens * 3.8)
    truncated_text = text[:char_limit].rstrip() + "\n...[Context truncated to meet input token limit]"
    new_tokens = estimate_tokens(truncated_text)
    return truncated_text, new_tokens

def clean_markdown_artifacts(text: Optional[str]) -> str:
    """Strips all markdown bold/italic asterisks, hash headers, and normalizes typography."""
    if not text:
        return ""
    import re
    # Remove markdown bold/italic asterisks (**, *, ***)
    cleaned = text.replace("**", "").replace("*", "")
    # Remove leading markdown headers (e.g., '### Heading' or '# Title')
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    # Remove markdown bullet hyphens or bullets at start of lines (- , • )
    cleaned = re.sub(r"^\s*[-•]\s*", "", cleaned, flags=re.MULTILINE)
    # Normalize unicode non-breaking hyphens and dashes to standard hyphens
    cleaned = cleaned.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    # Normalize unicode smart quotes and spaces
    cleaned = cleaned.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    cleaned = cleaned.replace("\u202f", " ").replace("\u00a0", " ")
    cleaned = cleaned.replace("\u2248", "~").replace("\u2265", ">=").replace("\u2264", "<=")
    return cleaned.strip()

class LLMClient:
    """Real-time LLM Client with explicit input and output token controls."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_input_tokens: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ):
        self.provider = (provider or settings.llm_provider).lower()
        self.model = model or settings.llm_model
        self.max_input_tokens = max_input_tokens or settings.llm_max_input_tokens
        self.max_output_tokens = max_output_tokens or settings.llm_max_output_tokens
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        
        # Resolve API keys
        if self.provider == "gemini":
            self.api_key = api_key or settings.gemini_api_key
        elif self.provider == "openai":
            self.api_key = api_key or settings.openai_api_key
        elif self.provider in ("groq", "grok"):
            self.api_key = api_key or settings.groq_api_key
        else:
            self.api_key = ""

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_input_tokens: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Dispatches real-time generation enforcing input and output token boundaries."""
        if not self.api_key or self.provider == "mock":
            return ""

        input_budget = max_input_tokens or self.max_input_tokens
        output_budget = max_output_tokens or self.max_output_tokens
        temp = temperature if temperature is not None else self.temperature

        # Strictly enforce Input Token budget
        safe_prompt, actual_input_tokens = cap_input_tokens(prompt, input_budget)

        raw_text = ""
        if self.provider == "gemini":
            raw_text = self._call_gemini(safe_prompt, system_instruction, output_budget, temp)
        elif self.provider == "openai":
            raw_text = self._call_openai(safe_prompt, system_instruction, output_budget, temp)
        elif self.provider in ("groq", "grok"):
            raw_text = self._call_groq(safe_prompt, system_instruction, output_budget, temp)
        else:
            return ""

        # Remove stray markdown bold asterisks (**) and clean formatting
        return clean_markdown_artifacts(raw_text)

    def _call_gemini(
        self,
        prompt: str,
        system_instruction: Optional[str],
        max_output_tokens: int,
        temperature: float
    ) -> str:
        """Calls Google Gemini API with exact token capping."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
                "topP": 0.95
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                elif response.status_code == 503 and attempt < max_retries - 1:
                    print(f"[LLMClient Gemini] High demand spike (503). Retrying in 1.5s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(1.5)
                    continue
                else:
                    print(f"[LLMClient Gemini Error] Status {response.status_code}: {response.text}")
                    return ""
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1.5)
                    continue
                print(f"[LLMClient Gemini Exception]: {e}")
                return ""
        return ""

    def _call_openai(
        self,
        prompt: str,
        system_instruction: Optional[str],
        max_output_tokens: int,
        temperature: float
    ) -> str:
        """Calls OpenAI Chat Completion API with exact token capping."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_output_tokens
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"[LLMClient OpenAI Error] Status {response.status_code}: {response.text}")
                return ""
        except Exception as e:
            print(f"[LLMClient OpenAI Exception]: {e}")
            return ""

    def _call_groq(
        self,
        prompt: str,
        system_instruction: Optional[str],
        max_output_tokens: int,
        temperature: float
    ) -> str:
        """Calls Groq Chat Completion API with exact token capping."""
        url = f"{settings.groq_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_output_tokens
        }
        if "openai" in self.model or "oss" in self.model or "gpt" in self.model:
            payload["reasoning_effort"] = "low"

        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                elif response.status_code in (429, 503) and attempt < max_retries - 1:
                    retry_wait = 2.5
                    try:
                        retry_after = response.headers.get("retry-after")
                        if retry_after:
                            retry_wait = max(2.0, float(retry_after))
                    except Exception:
                        pass
                    print(f"[LLMClient Groq] Rate limit ({response.status_code}). Pausing {retry_wait}s to refill tokens (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_wait)
                    continue
                else:
                    print(f"[LLMClient Groq Error] Status {response.status_code}: {response.text}")
                    return ""
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1.5)
                    continue
                print(f"[LLMClient Groq Exception]: {e}")
                return ""
        return ""

llm_client = LLMClient()

def get_llm_client() -> LLMClient:
    """Returns the singleton LLMClient instance."""
    return llm_client

