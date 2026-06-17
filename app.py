import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))
from src.database import Database
from src.conversation_manager import ConversationManager
from src.voice_handler import VoiceHandler
from src.utils import inject_custom_css

# Page Configuration
st.set_page_config(
    page_title="Pak China Traders - WhatsApp Automation",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject styling
inject_custom_css()

# Initialize Database
db = Database()
conv_manager = ConversationManager()
voice_handler = VoiceHandler()

# Header Section
st.markdown("""
<div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 25px;'>
    <div>
        <h1 style='margin: 0; font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #60efff 0%, #00ff87 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            Pak China Traders
        </h1>
        <p style='margin: 5px 0 0 0; color: #9ca3af; font-size: 1.1rem;'>
            WhatsApp Business & Voice Automation Center
        </p>
    </div>
    <div style='display: flex; align-items: center; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); padding: 8px 16px; border-radius: 30px;'>
        <div class="pulsing-dot" style='margin-right: 10px;'></div>
        <span style='color: #10b981; font-weight: 600; font-size: 0.9rem;'>SYSTEM ONLINE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# System Architecture & Stats Summary
cols = st.columns(4)

active_provider = db.get_setting("llm_provider") or "Gemini"
active_model = db.get_setting(f"{active_provider.lower()}_model") or "Not Set"

with cols[0]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Active AI Engine</div>
        <div class="metric-value">{active_provider}</div>
        <div class="metric-desc">Model: {active_model}</div>
    </div>
    """, unsafe_allow_html=True)

# Count total metrics from DB
with db.get_connection() as conn:
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM customers")
    total_cust = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM conversations WHERE sender = 'customer'")
    total_msgs = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM orders")
    total_orders = c.fetchone()[0]

with cols[1]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Registered Customers</div>
        <div class="metric-value">{total_cust}</div>
        <div class="metric-desc">WhatsApp interactions</div>
    </div>
    """, unsafe_allow_html=True)

with cols[2]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Inbound Messages</div>
        <div class="metric-value">{total_msgs}</div>
        <div class="metric-desc">Auto-replied by AI</div>
    </div>
    """, unsafe_allow_html=True)

with cols[3]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Booked Orders</div>
        <div class="metric-value">{total_orders}</div>
        <div class="metric-desc">Automated workflow sales</div>
    </div>
    """, unsafe_allow_html=True)

# Grid Layout for App Status & Interactive Simulator
left_col, right_col = st.columns([1, 1.3])

with left_col:
    st.subheader("⚙️ System Status")
    
    status_card = """
    <div class="glass-card" style="margin-bottom: 15px;">
        <h4 style="margin-top:0; color:#38bdf8;">🌐 Webhook Endpoints</h4>
        <div style="font-size:0.9rem; line-height:1.6;">
            <b>FastAPI Port:</b> <code>8000</code><br>
            <b>WhatsApp Webhook:</b> <code>/webhooks/whatsapp</code> (POST)<br>
            <b>Voice Webhook:</b> <code>/webhooks/voice</code> (POST)<br>
            <b>Voice Callback:</b> <code>/webhooks/voice/respond</code> (POST)<br>
        </div>
    </div>
    """
    st.markdown(status_card, unsafe_allow_html=True)
    
    # Check Twilio Configuration Status
    twilio_configured = False
    twilio_sid = db.get_setting("twilio_account_sid")
    if twilio_sid and len(twilio_sid) > 10 and "your_twilio" not in twilio_sid:
        twilio_configured = True
        
    status_color = "#34d399" if twilio_configured else "#fbbf24"
    status_text = "Live (Twilio Integration Connected)" if twilio_configured else "Simulation Mode (No Twilio API Keys)"
    
    twilio_card = f"""
    <div class="glass-card">
        <h4 style="margin-top:0; color:{status_color};">📞 Twilio WhatsApp Channel</h4>
        <div style="font-size:0.9rem; line-height:1.6;">
            <b>Status:</b> {status_text}<br>
            <b>Account SID:</b> <code>{twilio_sid[:8] if twilio_sid else 'None'}...</code><br>
            <b>Sender Number:</b> <code>{db.get_setting("twilio_phone_number") or 'whatsapp:+14155238886'}</code><br>
        </div>
    </div>
    """
    st.markdown(twilio_card, unsafe_allow_html=True)

    # Simulator Instructions
    st.markdown("""
    ### 🚀 Testing instructions
    Use the **Automation Simulator** on the right to test how the LLM processes messages.
    - Select **WhatsApp Chat** to simulate a conversation.
    - Try typing: _"I want to book 5 silk threads and deliver it to Office 402, Block A, Karachi."_
    - The AI will automatically extract the order, query the catalog prices, calculate the total cost, create a **Pending** order in the database, and return a **JazzCash** payment link simulation!
    """)

with right_col:
    st.subheader("🧪 Automation Simulator")
    
    tab_whatsapp, tab_voice = st.tabs(["💬 WhatsApp Chat Simulator", "📞 Voice Call Simulator"])
    
    with tab_whatsapp:
        st.caption("Simulate an incoming WhatsApp message from a customer and watch the bot process it.")
        
        sim_phone = st.text_input("Customer Phone Number", value="+923214567890", key="sim_phone")
        sim_name = st.text_input("Customer Name", value="Muhammad Ali", key="sim_name")
        sim_message = st.text_area("Customer Message", value="Aslam o Alaikum, what is the price of Silk Thread and can I book 3 of them?", height=80, key="sim_message")
        
        if st.button("Send Message", key="send_wa"):
            if not sim_message.strip():
                st.warning("Please type a message first.")
            else:
                with st.spinner("Processing through AI Engine..."):
                    # Process message
                    reply = conv_manager.process_incoming_message(
                        whatsapp_number=sim_phone,
                        message_text=sim_message,
                        customer_name=sim_name
                    )
                    
                    st.markdown("### 💬 Live Execution Log")
                    
                    # Sentiment and Intent Analysis Check
                    cat, sent = conv_manager.analyze_sentiment_and_intent(sim_message)
                    sentiment_color = "#34d399" if sent == "positive" else "#f87171" if sent == "negative" else "#9ca3af"
                    intent_color = "#38bdf8" if cat == "order" else "#a78bfa" if cat == "complaint" else "#f3f4f6"
                    
                    # Display metadata badge
                    st.markdown(f"""
                    <div style='display: flex; gap: 10px; margin-bottom: 15px;'>
                        <span style='background: rgba(56, 189, 248, 0.15); border: 1px solid {intent_color}; color: {intent_color}; padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;'>Intent: {cat.upper()}</span>
                        <span style='background: rgba(16, 185, 129, 0.15); border: 1px solid {sentiment_color}; color: {sentiment_color}; padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;'>Sentiment: {sent.upper()}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show conversation bubbles
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.03); border-radius:12px; padding:15px; border:1px solid rgba(255,255,255,0.05);">
                        <div style="margin-bottom:15px;">
                            <b style="color:#60efff;">🧑 {sim_name} ({sim_phone}):</b>
                            <p style="margin:5px 0 0 0; background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; display:inline-block;">{sim_message}</p>
                        </div>
                        <div>
                            <b style="color:#00ff87;">🤖 AI Assistant:</b>
                            <div style="margin:5px 0 0 0; background:rgba(0,255,135,0.08); border-left:4px solid #00ff87; padding:12px; border-radius:4px; white-space: pre-wrap;">{reply}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.success("Successfully processed message and saved to SQLite database! Check pages inside sidebar to view data.")

    with tab_voice:
        st.caption("Simulate an incoming Twilio voice call and speech recognition transcription.")
        
        sim_voice_phone = st.text_input("Caller Phone Number", value="+923009876543", key="sim_voice_phone")
        sim_voice_trans = st.text_area("Caller Spoken Transcription (Speech-to-Text Mock)", value="Hello, my sewing machine kit is delayed. Can you check where it is?", height=80, key="sim_voice_trans")
        
        if st.button("Simulate Call Answer", key="send_voice"):
            if not sim_voice_trans.strip():
                st.warning("Please enter transcription.")
            else:
                with st.spinner("Processing speech and creating response TwiML..."):
                    # Process call
                    twiml_res = voice_handler.process_voice_input_and_respond(
                        caller_number=sim_voice_phone,
                        transcription=sim_voice_trans,
                        call_sid="SIMULATED_CALL_12345"
                    )
                    
                    st.markdown("### 📞 Call Routing TwiML Response")
                    st.code(twiml_res, language="xml")
                    
                    # Extract raw text spoken by Polly
                    speech_text_match = [line for line in twiml_res.split("\n") if "<Say" in line]
                    speech_text = speech_text_match[0].replace('<Say voice="Polly.Aditi" language="en-IN">', '').replace('</Say>', '').strip() if speech_text_match else "Goodbye!"
                    
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.03); border-radius:12px; padding:15px; border:1px solid rgba(255,255,255,0.05); margin-top:10px;">
                        <div style="margin-bottom:15px;">
                            <b style="color:#60efff;">🗣️ Caller Spoke:</b>
                            <p style="margin:5px 0 0 0; background:rgba(255,255,255,0.05); padding:10px; border-radius:8px;">"{sim_voice_trans}"</p>
                        </div>
                        <div>
                            <b style="color:#38bdf8;">🔊 Text-To-Speech Output:</b>
                            <p style="margin:5px 0 0 0; background:rgba(56,189,248,0.1); border-left:4px solid #38bdf8; padding:10px; border-radius:4px;"><i>"{speech_text}"</i></p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.success("Successfully logged call details to calls database! Review the Call Logs under Dashboard/Analytics.")
