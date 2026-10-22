"""Groq-only text service used by chat and disease-summary routes.

The image is never sent to Groq. Disease summaries receive only the model's
class scores plus any short symptom text the user entered.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
DEFAULT_MODELS = (
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
)

_SYSTEM_PROMPT = (
    "তুমি বাংলাদেশের কৃষকদের জন্য ক্ষেতসাথী নামের একটি বাংলা কৃষি সহায়ক। "
    "সহজ, সম্মানজনক ও সংক্ষিপ্ত বাংলায় উত্তর দাও। সাধারণ চাষাবাদ, আবহাওয়া-সচেতন "
    "পরিকল্পনা এবং নিরাপদ পরবর্তী পদক্ষেপে সহায়তা করো। লাইভ বাজারদর, সরকারি তথ্য "
    "বা আবহাওয়া পাওয়া হয়েছে বলে দাবি কোরো না যদি সেগুলো অনুরোধে না থাকে। নমুনা বা "
    "সিমুলেটেড দামের কথা স্পষ্টভাবে নমুনা বলো। রোগের ছবি-ভিত্তিক শ্রেণিবিন্যাস নিশ্চিত "
    "রোগনির্ণয় নয়। কীটনাশক/সারের মাত্রা অনুমান করে বলবে না; স্থানীয় কৃষি কর্মকর্তা বা "
    "যোগ্য কৃষিবিদের পরামর্শ নিতে বলো।"
)

_model_cache: set[str] | None = None
_model_cache_expiry = 0.0


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def candidate_models(api_key: str) -> list[str]:
    """Prefer GPT-OSS, but use model IDs the current Groq key can see when possible."""
    global _model_cache, _model_cache_expiry

    configured = [os.getenv("GROQ_MODEL_PRIMARY", "openai/gpt-oss-120b")]
    configured.extend(
        os.getenv("GROQ_MODEL_FALLBACKS", "openai/gpt-oss-20b,llama-3.3-70b-versatile").split(",")
    )
    preferred = _unique(configured + list(DEFAULT_MODELS))

    now = time.monotonic()
    if _model_cache is None or now >= _model_cache_expiry:
        try:
            response = requests.get(
                GROQ_MODELS_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=(4, 7),
            )
            response.raise_for_status()
            payload = response.json()
            _model_cache = {
                item["id"] for item in payload.get("data", [])
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            }
            _model_cache_expiry = now + 900
        except (requests.RequestException, ValueError, TypeError, AttributeError):
            # Discovery is an optimization; completion fallback still runs.
            _model_cache = set()
            _model_cache_expiry = now + 60

    if _model_cache:
        ordered = [model for model in preferred if model in _model_cache]
        ordered.extend(sorted(
            model for model in _model_cache
            if model not in ordered
            and ("gpt-oss" in model.casefold() or "llama" in model.casefold())
        ))
        if ordered:
            return ordered[:3]
    return preferred[:3]


def _error_code(response: requests.Response) -> str:
    try:
        payload = response.json()
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, dict):
            return str(error.get("code") or error.get("type") or "")[:60]
    except (ValueError, requests.RequestException):
        pass
    return ""


def complete(messages: list[dict[str, str]], max_tokens: int = 700) -> tuple[str | None, str | None, str | None]:
    """Return ``(answer, model, error_code)``; never expose a secret in errors."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None, None, "missing_key"

    safe_messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for message in messages[-10:]:
        role = message.get("role")
        content = str(message.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            safe_messages.append({"role": role, "content": content[:3500]})
    if len(safe_messages) == 1:
        return None, None, "empty_messages"

    try:
        token_limit = min(max(int(max_tokens), 64), 1200)
    except (TypeError, ValueError):
        token_limit = 700

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Smart-Krishi-Buddhimotta/1.0",
    }
    last_error = "unavailable"
    for model in candidate_models(api_key):
        payload: dict[str, Any] = {"model": model, "messages": safe_messages}
        if "gpt-oss" in model.casefold():
            payload["max_completion_tokens"] = token_limit
            payload["reasoning_effort"] = "medium"
        else:
            payload["temperature"] = 0.35
            payload["max_tokens"] = token_limit

        try:
            response = requests.post(
                GROQ_CHAT_URL,
                headers=headers,
                json=payload,
                timeout=(6, 30),
            )
        except requests.Timeout:
            last_error = "timeout"
            continue
        except requests.RequestException:
            last_error = "network"
            continue

        if response.status_code in {401, 403}:
            return None, None, "invalid_key"
        if response.status_code == 429:
            last_error = "rate_limit"
            continue
        if response.status_code in {400, 404, 422}:
            last_error = _error_code(response) or f"model_{response.status_code}"
            continue
        if response.status_code >= 500:
            last_error = "provider_unavailable"
            continue
        if response.status_code >= 400:
            last_error = _error_code(response) or f"http_{response.status_code}"
            continue

        try:
            body = response.json()
            choices = body.get("choices") or []
            message = choices[0].get("message", {}) if choices else {}
            content = message.get("content", "")
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") for part in content if isinstance(part, dict)
                )
            answer = str(content or "").strip()
        except (ValueError, TypeError, AttributeError, KeyError, IndexError):
            answer = ""

        if answer:
            return answer, model, None
        last_error = "empty_reply"

    return None, None, last_error


def disease_summary(
    crop_label: str,
    disease_label: str,
    score_percent: float,
    alternatives: list[dict[str, Any]],
    symptom: str,
) -> tuple[str | None, str | None, str | None]:
    """Ask Groq for cautious text based on classification labels, never the image."""
    scores = "; ".join(
        f"{item.get('label', 'অজানা')}: {float(item.get('score_percent', 0)):.1f}%"
        for item in alternatives[:3]
    )
    user_text = (
        f"বিদ্যমান ছবির শ্রেণিবিন্যাস মডেলের ফল: ফসলের অনুমান {crop_label}; "
        f"সর্বোচ্চ শ্রেণি {disease_label}; মডেল স্কোর {score_percent:.1f}%; "
        f"শীর্ষ বিকল্প: {scores or 'নেই'}। ব্যবহারকারীর লেখা লক্ষণ: "
        f"{symptom.strip()[:500] or 'কোনো লক্ষণ লেখা হয়নি'}। "
        "এটি নিশ্চিত রোগনির্ণয় নয় এবং তুমি ছবিটি দেখোনি। বাংলায় ৩টি সতর্ক, "
        "সাধারণ যাচাই/পরবর্তী পদক্ষেপ দাও; নির্দিষ্ট কীটনাশক, ওষুধ বা মাত্রা বলবে না। "
        "স্কোরকে calibrated probability বা নির্ভুলতা বলে উপস্থাপন করবে না।"
    )
    return complete([{"role": "user", "content": user_text}], max_tokens=420)
