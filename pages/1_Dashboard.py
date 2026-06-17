import streamlit as st
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.database import Database
from src.utils import inject_custom_css

st.set_page_config(
    page_title="Dashboard - Pak China Traders",
    page_icon="📊",
    layout="wide"
)

inject_custom_css()

db = Database()

# Page Title
st.markdown("""
<div style='margin-bottom: 25px;'>
    <h1 style='margin: 0; font-size: 2.2rem; font-weight: 800; color: #ffffff;'>
        📊 Operations Dashboard
    </h1>
    <p style='margin: 5px 0 0 0; color: #9ca3af; font-size: 1rem;'>
        Real-time monitoring of WhatsApp automation, order flows, and call analytics.
    </p>
</div>
""", unsafe_allow_html=True)

# Query core statistics from DB
with db.get_connection() as conn:
    c = conn.cursor()
    # Customers
    c.execute("SELECT COUNT(*) FROM customers")
    total_cust = c.fetchone()[0]
    
    # Conversations
    c.execute("SELECT COUNT(*) FROM conversations WHERE sender = 'customer'")
    total_msgs_in = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM conversations WHERE sender = 'bot'")
    total_msgs_out = c.fetchone()[0]
    total_msgs = total_msgs_in + total_msgs_out
    
    # Orders
    c.execute("SELECT COUNT(*) FROM orders")
    total_orders = c.fetchone()[0]
    c.execute("SELECT SUM(total_amount) FROM orders")
    total_revenue = c.fetchone()[0] or 0.0
    c.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
    pending_orders = c.fetchone()[0]
    
    # Calls
    c.execute("SELECT COUNT(*) FROM calls")
    total_calls = c.fetchone()[0]

    # LLM usage
    c.execute("SELECT SUM(cost) FROM llm_usage")
    total_llm_cost = c.fetchone()[0] or 0.0

# Display Metric Cards
cols = st.columns(4)

with cols[0]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Total Revenue</div>
        <div class="metric-value">Rs. {total_revenue:,.2f}</div>
        <div class="metric-desc">From {total_orders} completed & pending orders</div>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Total Messages</div>
        <div class="metric-value">{total_msgs}</div>
        <div class="metric-desc">📥 In: {total_msgs_in} | 📤 Out: {total_msgs_out}</div>
    </div>
    """, unsafe_allow_html=True)

with cols[2]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Calls Handled</div>
        <div class="metric-value">{total_calls}</div>
        <div class="metric-desc">Transcribed & answered by TTS</div>
    </div>
    """, unsafe_allow_html=True)

with cols[3]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">LLM API Expenses</div>
        <div class="metric-value">${total_llm_cost:.4f}</div>
        <div class="metric-desc">Cost tracking per provider usage</div>
    </div>
    """, unsafe_allow_html=True)

# Detailed Status Sections
left_panel, right_panel = st.columns([1.2, 1])

with left_panel:
    st.subheader("🛍️ Recent Orders")
    orders = db.get_all_orders()
    
    if not orders:
        st.info("No orders booked yet. Use the Simulator on the Home page or receive automated WhatsApp customer orders.")
    else:
        # Construct Pandas DataFrame for visual representation
        order_list = []
        for o in orders[:5]:  # show top 5
            order_list.append({
                "Order ID": o["id"][:8] + "...",
                "Customer": o["customer_name"],
                "Phone": o["customer_phone"],
                "Amount": f"Rs. {o['total_amount']:,.2f}",
                "Status": o["status"].upper(),
                "Date": datetime.fromisoformat(o["created_at"]).strftime("%b %d, %I:%M %p")
            })
        df_orders = pd.DataFrame(order_list)
        st.dataframe(df_orders, use_container_width=True)
        st.markdown("[View All Orders Pages &rarr;](Orders)", unsafe_allow_html=True)

    st.subheader("📞 Recent Call Logs")
    calls = db.get_all_calls()
    if not calls:
        st.info("No incoming calls logged yet.")
    else:
        call_list = []
        for call in calls[:5]:
            call_list.append({
                "Caller": call["customer_name"],
                "Phone": call["customer_phone"],
                "Duration": f"{call['duration']}s",
                "Spoken Query": call["transcription"][:45] + "..." if len(call["transcription"]) > 45 else call["transcription"],
                "Time": datetime.fromisoformat(call["timestamp"]).strftime("%b %d, %I:%M %p")
            })
        df_calls = pd.DataFrame(call_list)
        st.dataframe(df_calls, use_container_width=True)

with right_panel:
    st.subheader("💬 Active Conversations")
    
    # Query database for recent messages across all customers
    with db.get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT conv.*, cust.name as customer_name, cust.whatsapp_number as customer_phone 
            FROM conversations conv 
            JOIN customers cust ON conv.customer_id = cust.id 
            ORDER BY conv.timestamp DESC 
            LIMIT 6
        """)
        recent_convs = [dict(row) for row in c.fetchall()]

    if not recent_convs:
        st.info("No conversations recorded yet.")
    else:
        for msg in recent_convs:
            sender_tag = "👤 Customer" if msg["sender"] == "customer" else "🤖 Bot"
            tag_color = "#38bdf8" if msg["sender"] == "customer" else "#10b981"
            
            # Format timestamp
            time_formatted = datetime.fromisoformat(msg["timestamp"]).strftime("%I:%M %p")
            
            st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <b style="color: {tag_color}; font-size: 0.9rem;">{sender_tag} - {msg['customer_name']}</b>
                    <span style="color: #6b7280; font-size: 0.8rem;">{time_formatted}</span>
                </div>
                <div style="font-size: 0.9rem; color: #d1d5db; line-height: 1.4;">{msg['message']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("[Open Inbox &rarr;](Conversations)", unsafe_allow_html=True)
