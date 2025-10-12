import os
import sys
from pathlib import Path

# 1) Update this path to your project directory on PythonAnywhere
#    Example: /home/<username>/myproject
PROJECT_HOME = os.environ.get("PROJECT_HOME", "/home/<username>/yourproject")

# Ensure the project directory is on sys.path and set as CWD
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

try:
    os.chdir(PROJECT_HOME)
except FileNotFoundError:
    # Fallback: use the directory of this WSGI file
    PROJECT_HOME = str(Path(__file__).resolve().parent)
    if PROJECT_HOME not in sys.path:
        sys.path.insert(0, PROJECT_HOME)
    os.chdir(PROJECT_HOME)

# 2) Optionally load environment variables from a .env in project root
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(PROJECT_HOME, ".env"), override=False)
except Exception:
    pass

# 3) Import the Flask app that bridges Telegram webhook -> PTB
#    We expose 'application' for the WSGI server
from webhook_app import application_wsgi as application
