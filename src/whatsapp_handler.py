import sys
from pathlib import Path
from twilio.rest import Client

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
from src.database import Database

class WhatsAppHandler:
    def __init__(self):
        self.db = Database()

    def send_message(self, to_number: str, message_body: str) -> bool:
        """
        Send a WhatsApp message using Twilio API.
        Retrieves credentials from SQLite settings dynamically, falling back to config.py.
        """
        # Format target phone number
        to_phone = to_number.strip().replace(" ", "")
        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"

        # Fetch Twilio settings from DB
        db_sid = self.db.get_setting("twilio_account_sid")
        db_token = self.db.get_setting("twilio_auth_token", decrypt=True)
        db_phone = self.db.get_setting("twilio_phone_number")

        # Resolve credentials: preference is DB > Config
        sid = db_sid if db_sid else TWILIO_ACCOUNT_SID
        token = db_token if db_token else TWILIO_AUTH_TOKEN
        from_phone = db_phone if db_phone else TWILIO_PHONE_NUMBER

        if not from_phone.startswith("whatsapp:"):
            from_phone = f"whatsapp:{from_phone}"

        print(f"\n--- [WhatsApp OUTBOX] ---")
        print(f"TO: {to_phone}")
        print(f"FROM: {from_phone}")
        print(f"MESSAGE: {message_body}")
        print(f"-------------------------\n")

        # Fallback simulation if credentials are empty
        if not sid or not token or "your_twilio" in sid or "your_twilio" in token:
            print("Twilio WhatsApp credentials not configured. Message simulated in logs successfully.")
            return True

        try:
            client = Client(sid, token)
            message = client.messages.create(
                body=message_body,
                from_=from_phone,
                to=to_phone
            )
            print(f"Twilio API Success: Message SID {message.sid}")
            return True
        except Exception as e:
            print(f"Twilio API Error sending message: {e}")
            return False
