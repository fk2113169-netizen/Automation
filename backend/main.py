import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from backend.webhooks import router as webhook_router

app = FastAPI(
    title="Pak China Traders WhatsApp Automation API",
    description="FastAPI backend for Twilio WhatsApp and Voice webhooks",
    version="1.0.0"
)

# Configure CORS for dashboards or testing tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register webhook endpoints
app.include_router(webhook_router)

@app.get("/")
async def root():
    """Service health and metadata check."""
    return {
        "service": "Pak China Traders WhatsApp Automation Webhook Backend",
        "status": "online",
        "endpoints": {
            "whatsapp_webhook": "/webhooks/whatsapp [POST]",
            "voice_webhook": "/webhooks/voice [POST]",
            "voice_respond": "/webhooks/voice/respond [POST]"
        }
    }
