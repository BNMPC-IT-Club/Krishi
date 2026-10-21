"""AI agri assistant — OpenRouter (gpt-oss-120b / gpt-oss-20b) with Groq fallback.

Key is read from secrets/env only (OPENROUTER_API_KEY or GROQ_API_KEY).
Nothing crashes without a key: callers show a setup message instead.
"""
import os

import requests

SYSTEM_PROMPT = (
    "তুমি 'স্মার্ট কৃষি বুদ্ধিমত্তা'-এর কৃষি সহায়ক। বাংলাদেশের প্রেক্ষাপটে ফসল চাষ, "
    "রোগ-বালাই, সার, সেচ, আবহাওয়া-নির্ভর পরিকল্পনা ও বাজারদর নিয়ে সাধারণ পরামর্শ দাও। "
    "উত্তর সহজ, ছোট ও ব্যবহারযোগ্য বাংলায় দাও (প্রয়োজনে ইংরেজি পরিভাষা ব্র্যাকেটে)। "
    "কখনোই নতুন বা লাইভ বাজারদর, তাপমাত্রা বা ডেটা উদ্ভাবন করো না; যদি প্রকৃত ডেটা "
    "প্রাসঙ্গে থাকে তবেই তা উদ্ধৃত করো এবং উৎস/তারিখ উল্লেখ করো। রোগ নির্ণয়ে নিশ্চিত "
    "হয়ে বলা এড়িয়ে চলো—প্রয়োজনে স্থানীয় কৃষি অফিস/বিশেষজ্ঞের পরামর্শ নিতে বলো। "
    "যদি ব্যবহারকারী ইংরেজিতে লেখে, ইংরেজিতেই উত্তর দাও।"
)

# Model preference order: OpenRouter gpt-oss family first, then Groq Llama.
_PROVIDERS = [
    # (env-key names, base_url, models to try in order)
    (["OPENROUTER_API_KEY", "openrouter_api_key"],
     "https://openrouter.ai/api/v1/chat/completions",
     ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]),
    (["GROQ_API_KEY", "groq_api_key"],
     "https://api.groq.com/openai/v1/chat/completions",
     ["llama-3.3-70b-versatile"]),
]


def _secrets_get(name):
    try:
        import streamlit as st
        v = st.secrets.get(name)
        return v
    except Exception:
        return None


def get_api_key():
    """Return (key, provider_name, base_url, models) for the first configured provider."""
    for env_names, url, models in _PROVIDERS:
        for n in env_names:
            key = os.getenv(n) or _secrets_get(n)
            if key:
                return key, n.split("_")[0].lower(), url, models
    return None, None, None, None


def has_key():
    key, *_ = get_api_key()
    return key is not None


def chat_completion(messages, system_prompt=None, temperature=0.4, max_tokens=900):
    """Send a chat completion request. Returns (reply_text, error_message).

    Tries each model of the configured provider in order (e.g. gpt-oss-120b,
    then gpt-oss-20b). Exactly one of reply/error is non-None.
    """
    key, provider, url, models = get_api_key()
    if not key:
        return None, ("⚙️ AI সহায়কের জন্য API key কনফিগার করা নেই। "
                      "`secrets.toml` বা Streamlit Cloud Settings-এ "
                      "`OPENROUTER_API_KEY` (console.openrouter.ai) যোগ করুন। "
                      "বাকি সব ফিচার স্বাভাবিক চলবে।")
    payload_base = {
        "messages": [{"role": "system",
                      "content": system_prompt or SYSTEM_PROMPT}] + list(messages),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/red1-for-hek/Smart-Krishi-Buddhimotta"
        headers["X-Title"] = "Smart Krishi Buddhimotta"
    last_err = None
    for model in models:
        try:
            r = requests.post(url, headers=headers,
                              json={"model": model, **payload_base}, timeout=60)
            if r.status_code == 429:
                return None, "🕐 ফ্রি-টিয়ার সীমা অতিক্রম করেছে। একটু পরে আবার চেষ্টা করুন।"
            if r.status_code in (403, 404):  # model unavailable → try next model
                last_err = f"{type(r).__name__}:{r.status_code}"
                continue
            r.raise_for_status()
            data = r.json()
            reply = (data["choices"][0]["message"]["content"] or "").strip()
            if reply:
                return reply, None
            last_err = "empty-reply"
        except requests.exceptions.RequestException as e:
            last_err = type(e).__name__
        except (KeyError, IndexError):
            last_err = "bad-payload"
    return None, (f"⚠️ AI সেবা এখন পাওয়া যাচ্ছে না ({last_err})। পরে আবার চেষ্টা করুন।")
