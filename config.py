import os
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Load .env file from the current directory
base_dir = Path(__file__).resolve().parent
env_path = base_dir / ".env"

if env_path.exists():
    load_dotenv(env_path)
else:
    # If .env doesn't exist, create it with a generated key
    key = Fernet.generate_key().decode()
    with open(env_path, "w") as f:
        f.write(f"ENCRYPTION_KEY={key}\n")
        f.write("DATABASE_PATH=whatsapp_automation.db\n")
        f.write("PORT=8000\n")
        f.write("WEBHOOK_URL=http://localhost:8000\n")
    load_dotenv(env_path)

DATABASE_PATH = os.getenv("DATABASE_PATH", "whatsapp_automation.db")
# Resolve database path relative to workspace
if not os.path.isabs(DATABASE_PATH):
    DATABASE_PATH = str(base_dir / DATABASE_PATH)

ENCRYPTION_KEY_STR = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY_STR:
    ENCRYPTION_KEY_STR = Fernet.generate_key().decode()

ENCRYPTION_KEY = ENCRYPTION_KEY_STR.encode()

# Twilio Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "whatsapp:+14155238886")
TWILIO_VOICE_NUMBER = os.getenv("TWILIO_VOICE_NUMBER", "")

# Webhook Settings
PORT = int(os.getenv("PORT", 8000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000")
