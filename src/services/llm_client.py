from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol
from urllib import request
from urllib.error import HTTPError, URLError

from src.utils.config import settings


@dataclass
class LLMResponse:
    text: str
    raw: dict


class SupportsGenerate(Protocol):
    def generate(self, prompt: str) -> LLMResponse: ...


class LLMClient:
    """Provider-neutral LLM client shell for mock and local OpenAI-compatible models."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        max_tokens: int = 350,
    ) -> None:
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model or "local-model"
        self.base_url = (base_url or settings.llm_base_url or "http://127.0.0.1:1234/v1").rstrip("/")
        self.api_key = settings.llm_api_key
        self.max_tokens = max_tokens

    def generate(
        self,
        prompt: str,
        *,
        response_schema: dict | None = None,
        response_schema_name: str = "structured_response",
    ) -> LLMResponse:
        if self.provider == "mock":
            return LLMResponse(
                text="Mock LLM response. 실제 매핑 분석은 local_openai 또는 다른 provider 설정 후 실행합니다.",
                raw={"provider": self.provider, "model": self.model, "prompt_length": len(prompt)},
            )
        if self.provider == "local_openai":
            return self._generate_local_openai(
                prompt,
                response_schema=response_schema,
                response_schema_name=response_schema_name,
            )
        raise NotImplementedError(f"LLM provider is not implemented yet: {self.provider}")

    def _generate_local_openai(
        self,
        prompt: str,
        *,
        response_schema: dict | None = None,
        response_schema_name: str = "structured_response",
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise software analysis assistant. Follow the user's requested output format.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        if response_schema is not None:
            schema_name = re.sub(r"[^a-zA-Z0-9_-]", "_", response_schema_name)[:64] or "structured_response"
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": response_schema,
                },
            }
        if "qwen3" in self.model.lower():
            payload["reasoning_effort"] = "none"
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


def generate_structured(
    llm_client: SupportsGenerate,
    prompt: str,
    *,
    schema: dict,
    schema_name: str,
) -> LLMResponse:
    """Use JSON Schema with the built-in client without breaking injected test clients."""
    if isinstance(llm_client, LLMClient):
        return llm_client.generate(
            prompt,
            response_schema=schema,
            response_schema_name=schema_name,
        )
    return llm_client.generate(prompt)
