# -----------------------------------------------------------------------------
# Telegram alert module for Smart Krishi Buddhimotta
# Free alternative to paid SMS alerts.
#
# SECURITY: The bot token is NEVER hardcoded here. It is read from
#   1) Streamlit secrets (st.secrets["telegram"]["bot_token"]) , or
#   2) environment variable TELEGRAM_BOT_TOKEN
#
# Setup:
#   1. You already created a bot with BotFather -> keep the token private.
#   2. Open your bot in Telegram and press /start (this registers your chat id).
#   3. In the app's Telegram section click "চ্যাট আইডি খুঁজে নিন" to auto-detect
#      your chat id, then save it in .streamlit/secrets.toml as chat_id.
# -----------------------------------------------------------------------------
import os
import requests

API_TIMEOUT = 10


def get_bot_token():
    """Read the Telegram bot token from Streamlit secrets or env."""
    try:
        import streamlit as st
        sec = st.secrets
        if "telegram" in sec and sec["telegram"].get("bot_token"):
            return str(sec["telegram"]["bot_token"]).strip()
        if sec.get("TELEGRAM_BOT_TOKEN"):
            return str(sec["TELEGRAM_BOT_TOKEN"]).strip()
    except Exception:
        pass
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def _api(token, method, params=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    r = requests.post(url, data=params or {}, timeout=API_TIMEOUT)
    try:
        data = r.json()
    except ValueError:
        return {"ok": False, "description": f"HTTP {r.status_code}: invalid response"}
    return data


def detect_chat_id(token):
    """Return the most recent chat id that messaged the bot (via getUpdates)."""
    data = _api(token, "getUpdates", {"timeout": 3})
    if not data.get("ok"):
        return None, data.get("description", "unknown error")
    updates = data.get("result", [])
    if not updates:
        return None, "no_updates"
    last = updates[-1]
    chat = (last.get("message") or last.get("channel_post") or {}).get("chat") or last.get("my_chat_member", {}).get("chat")
    if not chat:
        return None, "no_chat"
    return chat.get("id"), chat.get("first_name", "")


def send_telegram_alert(message, chat_id=None, token=None):
    """Send a plain-text alert. Returns (success: bool, detail: str)."""
    token = token or get_bot_token()
    if not token:
        return False, "Telegram bot টোকেন সেটআপ করা নেই।"
    if not chat_id:
        chat_id = None
        try:
            import streamlit as st
            sec = st.secrets
            if "telegram" in sec and sec["telegram"].get("chat_id"):
                chat_id = sec["telegram"]["chat_id"]
        except Exception:
            pass
        chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not chat_id:
        return False, "Chat ID সেট করা নেই — আগে বটে /start পাঠান ও চ্যাট আইডি সংরক্ষণ করুন।"
    try:
        data = _api(token, "sendMessage", {"chat_id": chat_id, "text": message, "disable_web_page_preview": True})
    except requests.exceptions.RequestException as e:
        return False, f"নেটওয়ার্ক ত্রুটি: {e}"
    if data.get("ok"):
        return True, "পাঠানো হয়েছে ✅"
    return False, data.get("description", "প্রেরণ ব্যর্থ")
