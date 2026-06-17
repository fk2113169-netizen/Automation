import sys
from pathlib import Path

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.database import Database
from src.llm_provider import get_active_provider
from src.utils import load_prompt_template

class VoiceHandler:
    def __init__(self):
        self.db = Database()

    def generate_welcome_twiml(self) -> str:
        """Generate TwiML XML to greet caller and gather speech transcription."""
        business_name = self.db.get_setting("business_name") or "Pak China Traders"
        
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="en-IN">Hello! Thank you for calling {business_name}. How can we help you today? Please speak after the beep.</Say>
    <Gather input="speech" action="/voice/respond" method="POST" speechTimeout="auto" timeout="4" language="en-US">
        <Play>http://demo.twilio.com/docs/classic.mp3</Play>
    </Gather>
    <Say voice="Polly.Aditi" language="en-IN">We did not receive any input. Thank you for calling, goodbye!</Say>
    <Hangup />
</Response>"""
        return twiml

    def process_voice_input_and_respond(self, caller_number: str, transcription: str, call_sid: str) -> str:
        """
        Process caller transcription, get response from active LLM, and log call.
        Returns TwiML response.
        """
        # Fetch or create customer record
        customer = self.db.get_or_create_customer(caller_number)
        customer_id = customer['id']

        if not transcription:
            transcription = "[No spoken input captured]"
            reply_text = "Sorry, I couldn't hear you clearly. Please try speaking again."
        else:
            # Render prompt template
            business_name = self.db.get_setting("business_name") or "Pak China Traders"
            prompt = load_prompt_template(
                "voice_call",
                business_name=business_name,
                transcription=transcription
            )

            try:
                # Call active LLM
                provider = get_active_provider()
                # Use a system prompt suited for voice
                reply_text = provider.get_response(
                    prompt=prompt,
                    conversation_history=[],
                    system_prompt="You are a voice phone assistant. Speak extremely briefly, conversational and clear. No markdown."
                )
            except Exception as e:
                print(f"Error generating voice response: {e}")
                reply_text = "Thank you for your response. We will contact you back via WhatsApp."

        # Clean reply_text for XML safety and speech synthesis (remove markdown characters)
        clean_reply = reply_text.replace("*", "").replace("#", "").replace("-", " ")

        # Log call (assuming duration 10s for demo/simulated logs, or Twilio CallDuration if available)
        self.db.log_call(
            customer_id=customer_id,
            duration=15,  # simulated duration in seconds
            transcription=transcription,
            recording_url=""
        )

        # Generate TwiML XML to speak the response and optionally allow further discussion
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="en-IN">{clean_reply}</Say>
    <Gather input="speech" action="/voice/respond" method="POST" speechTimeout="auto" timeout="4" language="en-US">
        <Say voice="Polly.Aditi" language="en-IN">If you have another question, please ask now. Otherwise, you can hang up.</Say>
    </Gather>
    <Say voice="Polly.Aditi" language="en-IN">Thank you for calling Pak China Traders. Goodbye!</Say>
    <Hangup />
</Response>"""
        return twiml
