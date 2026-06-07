from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import request
from urllib.error import HTTPError, URLError

from src.utils.config import settings


@dataclass
class LLMResponse:
    text: str
    raw: dict


class LLMClient:
    """Provider-neutral LLM client shell for mock and local OpenAI-compatible models."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model or "local-model"
        self.base_url = (base_url or settings.llm_base_url or "http://127.0.0.1:1234/v1").rstrip("/")
        self.api_key = settings.llm_api_key

    def generate(self, prompt: str) -> LLMResponse:
        if self.provider == "mock":
            return LLMResponse(
                text="Mock LLM response. 실제 매핑 분석은 local_openai 또는 다른 provider 설정 후 실행합니다.",
                raw={"provider": self.provider, "model": self.model, "prompt_length": len(prompt)},
            )
        if self.provider == "local_openai":
            return self._generate_local_openai(prompt)
        raise NotImplementedError(f"LLM provider is not implemented yet: {self.provider}")

    def _generate_local_openai(self, prompt: str) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise software analysis assistant. Return only the requested JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 350,
            "stream": False,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = request.Request(f"{self.base_url}/chat/completions", data=data, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Local LLM HTTP error {exc.code}: {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"Local LLM connection failed: {exc.reason}") from exc

        text = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        return LLMResponse(text=text, raw={"provider": self.provider, "model": self.model, "response": raw})
