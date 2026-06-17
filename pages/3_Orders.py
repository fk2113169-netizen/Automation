import streamlit as st
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.database import Database
from src.utils import inject_custom_css

st.set_page_config(
    page_title="Orders - Pak China Traders",
    page_icon="🛍️",
    layout="wide"
)

inject_custom_css()

db = Database()

# Page Title
st.markdown("""
<div style='margin-bottom: 25px;'>
    <h1 style='margin: 0; font-size: 2.2rem; font-weight: 800; color: #ffffff;'>
        🛍️ Order Fulfilment System
    </h1>
    <p style='margin: 5px 0 0 0; color: #9ca3af; font-size: 1rem;'>
        Review, confirm, and track orders extracted automatically by AI from conversations.
    </p>
</div>
""", unsafe_allow_html=True)

# Fetch orders from database
orders = db.get_all_orders()

# Metric Summary Cards
o_cols = st.columns(4)

total_count = len(orders)
pending_count = len([o for o in orders if o["status"] == "pending"])
confirmed_count = len([o for o in orders if o["status"] == "confirmed"])
completed_count = len([o for o in orders if o["status"] in ("shipped", "delivered")])

with o_cols[0]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Total Orders</div>
        <div class="metric-value">{total_count}</div>
        <div class="metric-desc">Lifetime orders processed</div>
    </div>
    """, unsafe_allow_html=True)

with o_cols[1]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Pending Extraction</div>
        <div class="metric-value" style="background: linear-gradient(135deg, #fbbf24 0%, #ff8787 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{pending_count}</div>
        <div class="metric-desc">Awaiting manual approval/payment</div>
    </div>
    """, unsafe_allow_html=True)

with o_cols[2]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Confirmed Queue</div>
        <div class="metric-value" style="background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{confirmed_count}</div>
        <div class="metric-desc">Approved for packaging</div>
    </div>
    """, unsafe_allow_html=True)

with o_cols[3]:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Dispatched / Completed</div>
        <div class="metric-value" style="background: linear-gradient(135deg, #34d399 0%, #60efff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{completed_count}</div>
        <div class="metric-desc">Shipped or delivered orders</div>
    </div>
    """, unsafe_allow_html=True)

# Main Section
status_tabs = st.tabs(["📋 All", "⌛ Pending", "✅ Confirmed", "🚚 Shipped", "📦 Delivered"])

def render_orders_list(filtered_orders):
    if not filtered_orders:
        st.info("No orders found matching this status.")
        return

    for o in filtered_orders:
        order_id = o["id"]
        customer_name = o["customer_name"]
        customer_phone = o["customer_phone"]
        total_amount = o["total_amount"]
        status = o["status"]
        date_str = datetime.fromisoformat(o["created_at"]).strftime("%b %d, %Y | %I:%M %p")
        
        # Load order json
        try:
            order_data = json.loads(o["order_json"])
        except Exception:
            order_data = {}

        # Badges
        status_colors = {
            "pending": "rgba(251, 191, 36, 0.2); border: 1px solid #fbbf24; color: #fbbf24;",
            "confirmed": "rgba(167, 139, 250, 0.2); border: 1px solid #a78bfa; color: #a78bfa;",
            "shipped": "rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; color: #38bdf8;",
            "delivered": "rgba(52, 211, 153, 0.2); border: 1px solid #34d399; color: #34d399;"
        }
        
        badge_style = status_colors.get(status, "rgba(255,255,255,0.1)")

        expander_title = f"📦 Order #{order_id[:8]} - {customer_name} (Rs. {total_amount:,.2f}) - {date_str}"
        
        with st.expander(expander_title):
            # Layout detail
            col_det1, col_det2 = st.columns(2)
            
            with col_det1:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 10px;">
                    <h5 style="margin-top: 0; color: #38bdf8;">👤 Customer Info</h5>
                    <b>Name:</b> {customer_name}<br>
                    <b>Phone:</b> {customer_phone}<br>
                    <b>Shipping Address:</b> {order_data.get('customer_address', 'Not Specified')}<br>
                    <b>Requested Delivery:</b> {order_data.get('delivery_date', 'None')}<br>
                    <b>Special Notes:</b> {order_data.get('special_notes', 'None')}<br>
                </div>
                """, unsafe_allow_html=True)
                
                # Payment & Tracking Simulated Links
                payment_link = f"https://jazzcash.com.pk/pay?order={order_id}&amount={total_amount}"
                tracking_link = f"https://pakchinatraders.com/track/{order_id}"
                
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                    <h5 style="margin-top: 0; color: #34d399;">🔗 Integration Links</h5>
                    <b>JazzCash Payment Link:</b> <a href="{payment_link}" target="_blank" style="color:#00ff87;">Click here to open pay portal</a><br>
                    <b>Shipping Tracking Link:</b> <a href="{tracking_link}" target="_blank" style="color:#60efff;">Track order route</a>
                </div>
                """, unsafe_allow_html=True)

            with col_det2:
                st.markdown("##### 🛒 Product Manifest")
                
                # Show products table
                products_list = order_data.get("products", [])
                if not products_list:
                    st.caption("No products parsed in this order.")
                else:
                    items_df = []
                    for item in products_list:
                        items_df.append({
                            "Item Name": item.get("name"),
                            "Quantity": item.get("quantity"),
                            "Unit Price": f"Rs. {item.get('unit_price'):,.2f}",
                            "Total Price": f"Rs. {item.get('total_price'):,.2f}"
                        })
                    st.table(pd.DataFrame(items_df))
                    
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 6px;">
                    <span style="font-weight:600; font-size: 0.95rem;">Current Status:</span>
                    <span style="font-weight:700; font-size: 0.9rem; padding: 4px 12px; border-radius: 12px; {badge_style}">{status.upper()}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Status update trigger buttons
                st.markdown("**Update Fulfiment Status:**")
                btn_cols = st.columns(3)
                
                with btn_cols[0]:
                    if status != "confirmed" and st.button("Mark Confirmed", key=f"conf_{order_id}"):
                        db.update_order_status(order_id, "confirmed")
                        st.success("Order confirmed!")
                        st.rerun()
                with btn_cols[1]:
                    if status != "shipped" and st.button("Mark Shipped", key=f"ship_{order_id}"):
                        db.update_order_status(order_id, "shipped")
                        st.success("Order marked shipped!")
                        st.rerun()
                with btn_cols[2]:
                    if status != "delivered" and st.button("Mark Delivered", key=f"del_{order_id}"):
                        db.update_order_status(order_id, "delivered")
                        st.success("Order marked delivered!")
                        st.rerun()

# Render content in tabs
with status_tabs[0]:
    render_orders_list(orders)

with status_tabs[1]:
    render_orders_list([o for o in orders if o["status"] == "pending"])

with status_tabs[2]:
    render_orders_list([o for o in orders if o["status"] == "confirmed"])

with status_tabs[3]:
    render_orders_list([o for o in orders if o["status"] == "shipped"])

with status_tabs[4]:
    render_orders_list([o for o in orders if o["status"] == "delivered"])
