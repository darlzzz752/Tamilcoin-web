import os
import threading
import asyncio
from typing import Optional

from flask import Flask, request, abort
from dotenv import load_dotenv

# Telegram imports
from telegram import Update
from telegram.ext import Application, CommandHandler

# Load environment variables from a .env file if present
load_dotenv()

# Import your existing bot logic (handlers, helpers, globals)
# NOTE: main.py must NOT execute code on import except definitions.
import main as bot  # noqa: E402

# --- Configuration ---
TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN") or getattr(bot, "TELEGRAM_BOT_TOKEN", None)
WEBHOOK_SECRET_PATH: str = os.getenv("WEBHOOK_SECRET_PATH", "telegram-webhook-secret-path-change-me")
WEBHOOK_SECRET_TOKEN: Optional[str] = os.getenv("WEBHOOK_SECRET_TOKEN")  # Optional, but recommended

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Configure it via environment or in main.py.")

# --- Build PTB Application and register handlers ---
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Reuse handlers defined in main.py
application.add_handler(CommandHandler("start", bot.start))
application.add_handler(CommandHandler("subscribe", bot.subscribe))
application.add_handler(CommandHandler("unsubscribe", bot.unsubscribe))
application.add_handler(CommandHandler("signals", bot.get_signals))
application.add_handler(CommandHandler("signal", bot.get_specific_signal))
# Admin commands
application.add_handler(CommandHandler("status", bot.status))
application.add_handler(CommandHandler("sureshot", bot.send_sure_shot_to_channel))
application.add_handler(CommandHandler("addsub", bot.add_subscriber_admin))

# --- Run Application on a dedicated asyncio loop in a background thread ---
_loop = asyncio.new_event_loop()


def _run_loop_forever() -> None:
    asyncio.set_event_loop(_loop)
    _loop.run_forever()


_bg_thread = threading.Thread(target=_run_loop_forever, name="ptb-event-loop", daemon=True)
_bg_thread.start()

# Initialize and start PTB application on the background loop
for _coro in (application.initialize(), application.start()):
    fut = asyncio.run_coroutine_threadsafe(_coro, _loop)
    fut.result(timeout=30)

# --- Flask app / WSGI entrypoint ---
app = Flask(__name__)


@app.get("/")
def healthcheck():
    return "OK", 200


@app.post(f"/{WEBHOOK_SECRET_PATH}")
def telegram_webhook():
    # Optional header verification for extra security (requires setWebhook with secret_token)
    if WEBHOOK_SECRET_TOKEN:
        header_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if header_token != WEBHOOK_SECRET_TOKEN:
            abort(401)

    data = request.get_json(force=True, silent=True)
    if data is None:
        abort(400)

    # Parse Update and hand over to PTB
    try:
        update = Update.de_json(data, application.bot)  # PTB v13/v20 compatibility
    except AttributeError:
        # Fallback for PTB versions using pydantic-style validation
        try:
            update = Update.model_validate(data)  # type: ignore[attr-defined]
        except Exception:
            abort(400)

    asyncio.run_coroutine_threadsafe(application.process_update(update), _loop)
    return "OK", 200


# Expose WSGI-compatible variable
# PythonAnywhere WSGI expects 'application' by default, but also accepts 'app'
application_wsgi = app
