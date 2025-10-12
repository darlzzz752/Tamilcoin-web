import os
import sys
import urllib.parse
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or getattr(__import__("main"), "TELEGRAM_BOT_TOKEN", None)
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")  # e.g. https://yourusername.pythonanywhere.com
WEBHOOK_SECRET_PATH = os.getenv("WEBHOOK_SECRET_PATH", "telegram-webhook-secret-path-change-me")
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")  # optional extra security


def main() -> int:
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set.")
        return 1
    if not WEBHOOK_BASE_URL:
        print("ERROR: WEBHOOK_BASE_URL is not set (e.g., https://<user>.pythonanywhere.com)")
        return 1

    url = f"{WEBHOOK_BASE_URL.rstrip('/')}/{urllib.parse.quote(WEBHOOK_SECRET_PATH)}"
    api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"

    payload = {"url": url}
    if WEBHOOK_SECRET_TOKEN:
        payload["secret_token"] = WEBHOOK_SECRET_TOKEN

    resp = requests.post(api, json=payload, timeout=30)
    try:
        data = resp.json()
    except Exception:
        print("Non-JSON response:", resp.text)
        return 1

    print(data)
    return 0 if data.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
