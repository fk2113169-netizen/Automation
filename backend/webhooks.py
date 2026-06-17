import sys
from pathlib import Path
from fastapi import APIRouter, Form, Response
from twilio.twiml.messaging_response import MessagingResponse

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.conversation_manager import ConversationManager
from src.voice_handler import VoiceHandler

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
conv_manager = ConversationManager()
voice_handler = VoiceHandler()

@router.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    ProfileName: str = Form(None)
):
    """
    Twilio WhatsApp Webhook.
    Called when a customer sends a message to the Twilio WhatsApp number.
    """
    # Clean up phone number: remove 'whatsapp:' prefix for processing if needed, 
    # but the manager handles it
    reply_text = conv_manager.process_incoming_message(
        whatsapp_number=From,
        message_text=Body,
        customer_name=ProfileName
    )

    # Return standard TwiML XML response for Twilio
    twiml = MessagingResponse()
    twiml.message(reply_text)
    
    return Response(content=str(twiml), media_type="application/xml")

@router.post("/voice")
async def voice_webhook():
    """
    Twilio Voice Incoming Call Webhook.
    Triggered when a phone call is received on the Twilio voice number.
    """
    twiml = voice_handler.generate_welcome_twiml()
    return Response(content=twiml, media_type="application/xml")

@router.post("/voice/respond")
async def voice_respond_webhook(
    From: str = Form(...),
    SpeechResult: str = Form(None),
    CallSid: str = Form(...)
):
    """
    Twilio Voice Speech Callback Webhook.
    Triggered when Twilio transcribes the user's spoken words.
    """
    twiml = voice_handler.process_voice_input_and_respond(
        caller_number=From,
        transcription=SpeechResult,
        call_sid=CallSid
    )
    return Response(content=twiml, media_type="application/xml")
