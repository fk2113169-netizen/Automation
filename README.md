# WhatsApp & Voice Automation Platform - Pak China Traders

This repository contains a production-ready, fully automated system for handling customer interactions, order extraction, voice routing, and live business configurations for Pak China Traders.

---

## 🛠️ Tech Stack & Features

- **Frontend Interface**: Streamlit dashboard with 5 specialized panels:
  - **Operations Dashboard**: General status monitoring, recent orders, active callers.
  - **Conversations Inbox**: Chat bubble interface, contact searches, manual overriding, exporting transcripts, and customer blocking.
  - **Order Booking**: Auto-extracted invoices with confidence ratings, unit pricing catalog verification, and JazzCash payment link simulations.
  - **Live Settings Panel**: Dynamic provider selection (OpenAI, Claude, Gemini, DeepSeek), live key testing, business hour policies, and catalog database administration.
  - **Business Analytics**: Plotly-powered charts illustrating inquiry conversion funnels, product metrics, line revenue trends, and LLM expenses.
- **Webhook API**: FastAPI backend routing incoming Twilio WhatsApp text events and IVR Voice Call speech callback flows.
- **Database**: SQLite tracking transactions, message context threads, speech transcription logs, and credentials (encrypted with `cryptography.fernet`).
- **AI Orchestration**: Unified multi-LLM connection using `litellm` standard interfaces.

---

## 📁 File Structure

```
whatsapp-automation/
├── app.py                          # Main Streamlit entrance & simulator panel
├── config.py                       # Application constants & encryption helpers
├── requirements.txt                # Pip requirements list
├── Dockerfile                      # Dual-port deployment wrapper container
├── README.md                       # Setup and operational instructions
├── .env.example                    # Sample environment keys
├── src/
│   ├── database.py                 # Thread-safe SQLite schemas & queries
│   ├── encryption.py               # Fernet AES API key security layers
│   ├── llm_provider.py             # LiteLLM routing, testing & billing calculations
│   ├── conversation_manager.py     # Context history loading & timezone auto-replies
│   ├── order_processor.py          # LLM invoice extraction & product matchers
│   ├── voice_handler.py            # TwiML XML speech generation and logging
│   ├── whatsapp_handler.py         # Twilio REST API transmission clients
│   └── utils.py                    # CSS styling and templates loading
├── prompts/                        # Custom Markdown instructions templates
│   ├── customer_support.md         # Inbound chat tone and catalog injection
│   ├── order_booking.md            # Inbound transaction JSON parser schema
│   ├── complaint_handling.md       # Escalation guidelines
│   └── voice_call.md               # Telephony speech generation limits
├── pages/                          # Multipage Streamlit tabs
│   ├── 1_Dashboard.py              # Main monitoring console
│   ├── 2_Conversations.py          # Message review & manual response override
│   ├── 3_Orders.py                 # Invoice status changes
│   ├── 4_Settings.py               # Key configuration & catalog tools
│   └── 5_Analytics.py              # Conversions, Sales, and Costs
└── backend/
    ├── main.py                     # Uvicorn FastAPI startup router
    └── webhooks.py                 # Endpoint callbacks (WhatsApp & Call gathers)
```

---

## 🚀 Quick Start (Local Setup)

### 1. Installation
Ensure Python 3.10+ is installed. Clone the repository and execute:
```bash
pip install -r requirements.txt
```

### 2. Startup Backend API (FastAPI)
Run the webhook server on port 8000 (required for Twilio webhooks):
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Startup Frontend Dashboard (Streamlit)
In a separate terminal shell, execute:
```bash
streamlit run app.py
```
This opens `http://localhost:8501` automatically.

---

## 🧪 Interactive Simulator Testing

To test the application without adding live API keys or setting up Twilio channels:
1. Open the main **Streamlit Portal** (`app.py` on port 8501).
2. Go to **Settings** and note that the database automatically seeds a product catalog (e.g. Silk Thread, Sewing machines).
3. Under the **💬 WhatsApp Chat Simulator** on the main Home screen:
   - Input a message like: *"Hi, I want to book 5 Silk Threads. Send it to Block C, Gulshan, Karachi."*
   - Submit the message. The chatbot will classify the intent as `order`, automatically match "Silk Thread" to the catalog price, write a **Pending** order inside the SQLite database, and return a formatted receipt containing a simulated **JazzCash** payment url.
4. Check the **Orders**, **Conversations**, and **Dashboard** tabs via the sidebar to watch the database change immediately.

---

## 📞 Connecting Live Twilio Channels

1. Start your API backend publicly (e.g. using `ngrok http 8000` to create an HTTPS tunnel).
2. Note the public URL (e.g., `https://xxxx.ngrok-free.app`).
3. Set your Twilio sandbox configuration paths:
   - **WhatsApp Sandbox Webhook**: `https://xxxx.ngrok-free.app/webhooks/whatsapp` (HTTP POST)
   - **Inbound Calls Voice Webhook**: `https://xxxx.ngrok-free.app/webhooks/voice` (HTTP POST)
4. Go to **Settings** inside the Streamlit panel:
   - Add your Twilio Account SID and Auth Token (stored securely using Fernet encryption).
   - Input your Twilio phone numbers.
   - Save. All WhatsApp replies and voice transcriptions will now routing live through Twilio!
