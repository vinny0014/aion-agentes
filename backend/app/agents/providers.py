import os
"""Provedores de IA — chamadas reais via httpx, prontas para ativar com API key.

Sem nenhuma chave configurada, o pipeline usa o modo offline: gera um rascunho
estruturado (esqueleto editorial) para que a produção diária nunca pare, e o
artigo aguarda revisão humana ou geração por IA quando a chave for adicionada.
"""
import re
import unicodedata

import httpx

from ..core.config import settings

TIMEOUT = 60.0


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:200] or "artigo"


LAST_USAGE = {"tokens": 0}


def _openai_compat(url: str, key: str, model: str, prompt: str, extra_headers: dict | None = None) -> str:
    """Chat Completions compatível: OpenAI e OpenRouter. Registra tokens reais."""
    headers = {"Authorization": f"Bearer {key}", **(extra_headers or {})}
    r = httpx.post(url, headers=headers, timeout=TIMEOUT, json={
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1200,
    })
    r.raise_for_status()
    body = r.json()
    LAST_USAGE["tokens"] = int(body.get("usage", {}).get("total_tokens", 0))
    return body["choices"][0]["message"]["content"]


def _anthropic(prompt: str) -> str:
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        timeout=TIMEOUT,
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"])


def _gemini(prompt: str) -> str:
    r = httpx.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        params={"key": settings.GEMINI_API_KEY},
        timeout=TIMEOUT,
        json={"contents": [{"parts": [{"text": prompt}]}]},
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def generate(provider: str, prompt: str) -> str:
    """Despacha para o provedor configurado. Lança httpx.HTTPError em falhas."""
    if provider == "openai":
        return _openai_compat(
            "https://api.openai.com/v1/chat/completions",
            settings.OPENAI_API_KEY, "gpt-4o-mini", prompt)  # modelo econômico por padrão
    if provider == "openrouter":
        return _openai_compat(
            "https://openrouter.ai/api/v1/chat/completions",
            settings.OPENROUTER_API_KEY, "anthropic/claude-sonnet-4",
            prompt, {"HTTP-Referer": os.environ.get("SITE_URL", "https://wordbet.com.br")})
    if provider == "anthropic":
        return _anthropic(prompt)
    if provider == "gemini":
        return _gemini(prompt)
    raise ValueError(f"Provedor desconhecido: {provider}")


def offline_draft(topic: str, template: str) -> dict:
    """Rascunho estruturado gerado localmente — mantém a produção diária ativa
    mesmo sem provedor de IA configurado."""
    corpo = (
        f"## Introduction\n\n"
        f"[Auto draft — awaiting final copy] Explain why \"{topic}\" "
        f"matters now and what the reader will learn.\n\n"
        f"## Overview\n\n"
        f"[Develop the core facts and concepts of {topic}.]\n\n"
        f"## In practice\n\n"
        f"[Bring concrete examples, applications or implications.]\n\n"
        f"## Conclusion\n\n"
        f"[Summarize the key points and suggest next steps for the reader.]"
    )
    return {
        "title": topic.strip().capitalize(),
        "slug": slugify(topic),
        "body": corpo,
        "excerpt": f"Rascunho editorial sobre {topic} aguardando redação final.",
        "template": template,
    }
