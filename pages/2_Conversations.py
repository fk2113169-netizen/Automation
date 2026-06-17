import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.database import Database
from src.whatsapp_handler import WhatsAppHandler
from src.utils import inject_custom_css

st.set_page_config(
    page_title="Conversations - Pak China Traders",
    page_icon="💬",
    layout="wide"
)

inject_custom_css()

db = Database()
wa_handler = WhatsAppHandler()

# Page Title
st.markdown("""
<div style='margin-bottom: 25px;'>
    <h1 style='margin: 0; font-size: 2.2rem; font-weight: 800; color: #ffffff;'>
        💬 Customer Chat & Inbox
    </h1>
    <p style='margin: 5px 0 0 0; color: #9ca3af; font-size: 1rem;'>
        Review automated AI discussions, block customers, or send manual message updates.
    </p>
</div>
""", unsafe_allow_html=True)

# Main Grid Layout
left_panel, right_panel = st.columns([1, 2.2])

with left_panel:
    st.subheader("👥 Contacts")
    
    # Customer Search
    search_query = st.text_input("🔍 Search customers...", value="", key="search_query").strip().lower()
    
    # Load all customers
    customers = db.get_all_customers()
    
    # Filter customers if searched
    filtered_customers = []
    for c in customers:
        name_match = search_query in c["name"].lower() if c["name"] else False
        phone_match = search_query in c["whatsapp_number"].lower()
        if name_match or phone_match or not search_query:
            filtered_customers.append(c)

    if not filtered_customers:
        st.info("No customers found.")
        selected_customer = None
    else:
        # Custom selector layout
        selected_index = 0
        customer_options = []
        for i, c in enumerate(filtered_customers):
            block_label = " 🚫[BLOCKED]" if c["blocked"] == 1 else ""
            label = f"{c['name']} ({c['whatsapp_number']}){block_label}"
            customer_options.append((i, label, c))
            
        selected_tuple = st.radio(
            "Select customer conversation:",
            options=customer_options,
            format_func=lambda x: x[1],
            label_visibility="collapsed"
        )
        selected_customer = selected_tuple[2] if selected_tuple else None

# Conversations View
with right_panel:
    if not selected_customer:
        st.info("Please select a customer from the left contacts panel to view the chat.")
    else:
        c_id = selected_customer["id"]
        c_phone = selected_customer["whatsapp_number"]
        c_name = selected_customer["name"]
        is_blocked = selected_customer["blocked"] == 1

        # Customer Meta Card
        blocked_badge = "<span style='background:rgba(239,68,68,0.2); border:1px solid #ef4444; color:#ef4444; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;'>BLOCKED</span>" if is_blocked else "<span style='background:rgba(16,185,129,0.2); border:1px solid #10b981; color:#10b981; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;'>ACTIVE</span>"
        
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 18px; border-radius: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0; color: #ffffff;">👤 {c_name}</h3>
                <code style="color: #38bdf8; font-size: 0.95rem;">{c_phone}</code>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                {blocked_badge}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Action Buttons (Block/Unblock, Export Transcript)
        act_col1, act_col2 = st.columns(2)
        
        with act_col1:
            if is_blocked:
                if st.button("🔓 Unblock Customer", use_container_width=True):
                    db.update_customer_block_status(c_id, blocked=False)
                    st.success("Customer unblocked successfully!")
                    st.rerun()
            else:
                if st.button("🚫 Block Customer", use_container_width=True):
                    db.update_customer_block_status(c_id, blocked=True)
                    st.warning("Customer blocked. Automated replies will not be sent.")
                    st.rerun()

        # Load conversation history (showing up to 50 messages)
        history = db.get_conversation_history(c_id, limit=50)

        with act_col2:
            # Build text transcript for export
            transcript_text = f"CONVERSATION TRANSCRIPT: {c_name} ({c_phone})\n"
            transcript_text += f"Date: {datetime.now().strftime('%c')}\n"
            transcript_text += "="*40 + "\n\n"
            for m in history:
                sender = "CUSTOMER" if m["sender"] == "customer" else "SUPPORT BOT"
                time_str = datetime.fromisoformat(m["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                transcript_text += f"[{time_str}] {sender}: {m['message']}\n\n"
                
            st.download_button(
                label="📥 Export Chat Transcript",
                data=transcript_text,
                file_name=f"transcript_{c_phone.replace('+', '')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.write("---")
        
        # Chat Bubbles View
        chat_container = st.container()
        with chat_container:
            if not history:
                st.caption("No messages exchanged yet.")
            else:
                for m in history:
                    # Styling for bubbles
                    align = "flex-start" if m["sender"] == "customer" else "flex-end"
                    bg_color = "rgba(255,255,255,0.05)" if m["sender"] == "customer" else "rgba(0, 255, 135, 0.08)"
                    border = "1px solid rgba(255,255,255,0.08)" if m["sender"] == "customer" else "1px solid rgba(0,255,135,0.2)"
                    text_color = "#ffffff"
                    sender_label = "👤 Customer" if m["sender"] == "customer" else "🤖 Support Bot"
                    sentiment_indicator = ""
                    
                    if m["sender"] == "customer" and m.get("sentiment"):
                        sent = m["sentiment"]
                        sent_emoji = "😊" if sent == "positive" else "😡" if sent == "negative" else "😐"
                        sentiment_indicator = f" <span style='font-size: 0.8rem; opacity: 0.7;'>({sent_emoji} {sent})</span>"

                    time_formatted = datetime.fromisoformat(m["timestamp"]).strftime("%b %d, %I:%M %p")
                    
                    st.markdown(f"""
                    <div style="display: flex; flex-direction: column; align-items: {align}; margin-bottom: 12px; width: 100%;">
                        <div style="max-width: 75%; background: {bg_color}; border: {border}; border-radius: 12px; padding: 12px 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <div style="display: flex; justify-content: space-between; gap: 30px; margin-bottom: 4px;">
                                <span style="font-weight: 700; font-size: 0.8rem; color: #9ca3af;">{sender_label}{sentiment_indicator}</span>
                                <span style="font-size: 0.75rem; color: #6b7280;">{time_formatted}</span>
                            </div>
                            <div style="color: {text_color}; font-size: 0.95rem; line-height: 1.4; white-space: pre-wrap;">{m['message']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.write("---")
        
        # Manual Message Reply Box
        if is_blocked:
            st.warning("Cannot send manual messages to blocked customers. Please unblock first.")
        else:
            st.subheader("✉️ Send Manual Message")
            manual_reply_body = st.text_area("Type your message here...", value="", height=80, placeholder="Write standard response or shipping updates...")
            
            if st.button("Send WhatsApp Message", key="send_manual"):
                if not manual_reply_body.strip():
                    st.warning("Please type a message before sending.")
                else:
                    with st.spinner("Sending message..."):
                        # Send WhatsApp message via handler (Twilio/Mock)
                        success = wa_handler.send_message(
                            to_number=c_phone,
                            message_body=manual_reply_body
                        )
                        
                        if success:
                            # Log manual message into database
                            db.add_message(
                                customer_id=c_id,
                                message=manual_reply_body,
                                sender="bot",
                                sentiment="neutral",
                                processed=True
                            )
                            st.success("Manual WhatsApp response sent and logged successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to send message via Twilio API. Check settings and API logs.")
