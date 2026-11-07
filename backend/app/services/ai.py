from typing import Any

import httpx

from app.config import Settings


SYSTEM_PROMPT = """You are Nyaya-Sahayak, a careful legal information assistant focused primarily on India.
Give clear, complete, plain-language educational information, not a lawyer-client opinion.

Answer every part of the user's question. Start with a direct answer, then give the reasoning or
explanation, and finish with practical next steps, important exceptions, or limitations when relevant.
Use short Markdown headings, paragraphs, numbered steps, and bullet lists so the answer is easy to scan.
Define legal terms in simple language. Do not be unnecessarily brief, but do not add irrelevant material.
If the question is ambiguous, state the assumption you are making or ask one concise clarifying question.

Never invent statutes, sections, judgments, citations, deadlines, or facts. Do not present uncertain
information as certain. If the answer depends on current law or specific facts, say so and suggest
checking an official source or consulting a qualified Indian lawyer. Keep the distinction between general
legal information and legal advice clear."""


class AIService:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(self.settings.ai_api_key)

    async def complete(self, messages: list[dict[str, str]]) -> str:
        if not self.configured:
            return (
                "AI provider is not configured yet. Add an API key to `backend/.env` using the "
                "free-tier provider settings in the README, then restart the backend."
            )
        url = f"{self.settings.ai_base_url.rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.settings.ai_model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
            "temperature": 0.2,
            "max_tokens": 1800,
        }
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.settings.ai_api_key}"},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("The configured AI provider could not complete the request.") from exc
