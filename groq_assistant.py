"""Groq-based agri assistant (replaces the old paid Gemini integration).

- Reads GROQ_API_KEY from st.secrets / environment — never hardcoded.
- Falls back to a plain `requests` call if the groq SDK is unavailable.
- If no key is configured, callers must show a setup message; nothing crashes.
"""
import os
import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

SYSTEM_PROMPT = (
    "তুমি 'স্মার্ট কৃষি বুদ্ধিমত্তা'-এর কৃষি সহায়ক। বাংলাদেশের প্রেক্ষাপটে ফসল চাষ, "
    "রোগ-বালাই, সার, সেচ, আবহাওয়া-নির্ভর পরিকল্পনা ও বাজারদর নিয়ে সাধারণ পরামর্শ দাও। "
    "উত্তর সহজ, ছোট ও ব্যবহারযোগ্য বাংলায় দাও (প্রয়োজনে ইংরেজি পরিভাষা ব্র্যাকেটে)। "
    "কখনোই নতুন বা লাইভ বাজারদর, তাপমাত্রা বা ডেটা উদ্ভাবন করো না; যদি প্রকৃত ডেটা "
    "প্রাসঙ্গে থাকে তবেই তা উদ্ধৃত করো এবং উৎস/তারিখ উল্লেখ করো। রোগ নির্ণয়ে নিশ্চিত "
    "হয়ে বলা এড়িয়ে চলো—প্রয়োজনে স্থানীয় কৃষি অফিস/বিশেষজ্ঞের পরামর্শ নিতে বলো। "
    "যদি ব্যবহারকারী ইংরেজিতে লেখে, ইংরেজিতেই উত্তর দাও।"
)


def get_groq_key():
    """Return the API key from secrets/env or None."""
    try:
        key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not key:
            try:
                key = st_secrets().get("GROQ_API_KEY") or st_secrets().get("OPENAI_API_KEY")
            except Exception:
                key = None
        return key or None
    except Exception:
        return None


def st_secrets():
    import streamlit as st
    return st.secrets


def chat_completion(messages, api_key=None, temperature=0.4, max_tokens=900):
    """Send a chat completion request. Returns (reply_text, error_message).

    Exactly one of them is non-None. Handles missing key, rate limits and
    network errors gracefully so the app never crashes.
    """
    api_key = api_key or get_groq_key()
    if not api_key:
        return None, (
            "⚙️ AI সহায়কের জন্য API key কনফিগার করা নেই। "
            "`.streamlit/secrets.toml`-এ `GROQ_API_KEY` বা `OPENAI_API_KEY` যোগ করুন; "
            "এবং Groq/AI provider-এ ফ্রি key নিন। বাকি সব ফিচার স্বাভাবিক চলবে。"
        )

    last_error = None
    for model_name in GROQ_MODELS:
        payload = {
            "model": model_name,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            r = requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"},
                json=payload, timeout=45,
            )
            if r.status_code == 429:
                return None, "🕐 ফ্রি-টিয়ার সীমা অতিক্রম করেছে। একটু পরে আবার চেষ্টা করুন।"
            if r.status_code in (400, 404):
                last_error = f"মডেল {model_name} গ্রহণ করা হয়নি"
                continue
            r.raise_for_status()
            data = r.json()
            reply = data["choices"][0]["message"]["content"].strip()
            return reply, None
        except requests.exceptions.RequestException as e:
            last_error = f"{type(e).__name__}: {e}"
            continue
        except (KeyError, IndexError, TypeError):
            last_error = "এআই সাড়া ঠিকভাবে পড়া যায়নি"
            continue

    if last_error:
        return None, f"⚠️ AI সেবা এখন পাওয়া যাচ্ছে না ({last_error})। কিছুক্ষণ পরে আবার চেষ্টা করুন।"
    return None, "⚠️ AI সেবা এখন পাওয়া যাচ্ছে না। পরে আবার চেষ্টা করুন।"
