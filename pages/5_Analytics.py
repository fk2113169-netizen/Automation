import streamlit as st
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta

# Add root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.database import Database
from src.utils import inject_custom_css

st.set_page_config(
    page_title="Analytics - Pak China Traders",
    page_icon="📈",
    layout="wide"
)

inject_custom_css()

db = Database()

# Page Title
st.markdown("""
<div style='margin-bottom: 25px;'>
    <h1 style='margin: 0; font-size: 2.2rem; font-weight: 800; color: #ffffff;'>
        📈 Performance & Cost Analytics
    </h1>
    <p style='margin: 5px 0 0 0; color: #9ca3af; font-size: 1rem;'>
        Review message statistics, sales conversions, and LLM expenses per provider.
    </p>
</div>
""", unsafe_allow_html=True)

# Toggle to inject simulated history for visualization
use_demo_data = st.checkbox("🔮 Populate with Demo Historical Data (For Visual Evaluation)", value=True)

# Load data
with db.get_connection() as conn:
    df_usage_db = pd.read_sql_query("SELECT * FROM llm_usage", conn)
    df_orders_db = pd.read_sql_query("SELECT * FROM orders", conn)
    df_conv_db = pd.read_sql_query("SELECT * FROM conversations", conn)
    df_calls_db = pd.read_sql_query("SELECT * FROM calls", conn)

# ----------------- DATA RESOLVER: LIVE OR MOCK -----------------
if use_demo_data:
    # 1. Mock LLM Cost Data
    mock_usage = [
        {"provider": "Gemini", "model": "gemini-1.5-flash", "cost": 0.045, "prompt_tokens": 150000, "completion_tokens": 80000, "timestamp": (datetime.now() - timedelta(days=i)).isoformat()} for i in range(15)
    ] + [
        {"provider": "OpenAI", "model": "gpt-4o-mini", "cost": 0.082, "prompt_tokens": 120000, "completion_tokens": 90000, "timestamp": (datetime.now() - timedelta(days=i)).isoformat()} for i in range(15)
    ] + [
        {"provider": "Claude", "model": "claude-3-5-sonnet-20240620", "cost": 0.420, "prompt_tokens": 60000, "completion_tokens": 15000, "timestamp": (datetime.now() - timedelta(days=i)).isoformat()} for i in range(15)
    ]
    df_usage = pd.DataFrame(mock_usage)

    # 2. Mock Order Data
    mock_orders = []
    products_pool = ["Silk Thread", "Polyester Fabric", "Sewing Machine Kit", "Cotton Knitted Yarn", "Industrial Needles"]
    prices_pool = [450.0, 1200.0, 18500.0, 800.0, 350.0]
    
    for i in range(30):
        prod_idx = i % len(products_pool)
        qty = (i % 3) + 1
        amount = prices_pool[prod_idx] * qty
        status = "delivered" if i < 20 else "shipped" if i < 25 else "confirmed" if i < 28 else "pending"
        mock_orders.append({
            "id": f"order_{i}",
            "total_amount": amount,
            "status": status,
            "product_name": products_pool[prod_idx],
            "quantity": qty,
            "created_at": (datetime.now() - timedelta(days=i//2)).isoformat()
        })
    df_orders = pd.DataFrame(mock_orders)

    # 3. Mock Conversations & Call Stats
    total_inbound = 450
    total_outbound = 520
    total_calls_count = 64
else:
    # Use real DB data
    df_usage = df_usage_db
    df_orders = df_orders_db
    total_inbound = len(df_conv_db[df_conv_db["sender"] == "customer"]) if not df_conv_db.empty else 0
    total_outbound = len(df_conv_db[df_conv_db["sender"] == "bot"]) if not df_conv_db.empty else 0
    total_calls_count = len(df_calls_db) if not df_calls_db.empty else 0

# ----------------- ANALYTICS SECTIONS -----------------
col_metrics1, col_metrics2 = st.columns(2)

with col_metrics1:
    st.markdown("### 📈 Funnel & Conversion Rates")
    
    # Calculate conversion: Customer Inquiries -> Orders
    orders_count = len(df_orders) if not df_orders.empty else 0
    inquiries_count = total_inbound
    
    conversion_rate = (orders_count / inquiries_count * 100) if inquiries_count > 0 else 0.0
    
    # Funnel Chart
    funnel_data = dict(
        number=[inquiries_count, inquiries_count * 0.4, orders_count],
        stage=["Inbound Inquiries", "Order Negotiations", "Booked Sales Orders"]
    )
    fig_funnel = px.funnel(funnel_data, x='number', y='stage', color_discrete_sequence=px.colors.sequential.Cyan_r)
    fig_funnel.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#ffffff", margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_funnel, use_container_width=True)
    
    st.markdown(f"""
    <div class="glass-card" style="text-align: center; padding: 15px !important;">
        <span style="color:#9ca3af; font-size:0.9rem;">CONVERSATION CONVERSION RATE</span>
        <h2 style="margin: 5px 0 0 0; color:#34d399; font-size:2.2rem; font-weight:800;">{conversion_rate:.1f}%</h2>
        <span style="font-size:0.8rem; color:#6b7280;">Percentage of inbound chat numbers placing at least 1 order</span>
    </div>
    """, unsafe_allow_html=True)

with col_metrics2:
    st.markdown("### 💰 LLM Engine Costs ($)")
    
    if df_usage.empty:
        st.info("No LLM usage logs recorded yet.")
    else:
        # Cost by provider bar chart
        df_costs_grouped = df_usage.groupby("provider")["cost"].sum().reset_index()
        fig_costs = px.bar(
            df_costs_grouped, 
            x="provider", 
            y="cost", 
            color="provider",
            labels={"provider": "LLM Provider", "cost": "Accumulated Expenses ($)"},
            color_discrete_map={"Gemini": "#a855f7", "OpenAI": "#10b981", "Claude": "#f97316", "DeepSeek": "#3b82f6"}
        )
        fig_costs.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#ffffff", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_costs, use_container_width=True)
        
        # Token metrics display
        total_tokens = df_usage["prompt_tokens"].sum() + df_usage["completion_tokens"].sum()
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 15px !important;">
            <span style="color:#9ca3af; font-size:0.9rem;">TOTAL API TOKENS CONSUMED</span>
            <h2 style="margin: 5px 0 0 0; color:#38bdf8; font-size:2.2rem; font-weight:800;">{total_tokens:,}</h2>
            <span style="font-size:0.8rem; color:#6b7280;">Input & response generated tokens</span>
        </div>
        """, unsafe_allow_html=True)

st.write("---")

col_charts1, col_charts2 = st.columns(2)

with col_charts1:
    st.markdown("### 📦 Product Sales Distribution")
    
    if df_orders.empty:
        st.info("No sales recorded.")
    else:
        # Group by product name
        # If live, order_json needs to be parsed, but demo has product_name column
        if use_demo_data:
            df_p_sales = df_orders.groupby("product_name")["quantity"].sum().reset_index()
            x_val = "product_name"
        else:
            # Live parsing of product list inside json
            parsed_items = []
            for _, row in df_orders.iterrows():
                try:
                    js = json.loads(row["order_json"])
                    for p in js.get("products", []):
                        parsed_items.append({"name": p["name"], "quantity": p["quantity"]})
                except Exception:
                    pass
            if parsed_items:
                df_p_sales = pd.DataFrame(parsed_items).groupby("name")["quantity"].sum().reset_index()
                x_val = "name"
            else:
                df_p_sales = pd.DataFrame()
                
        if not df_p_sales.empty:
            fig_p_sales = px.pie(
                df_p_sales, 
                values="quantity", 
                names=x_val, 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_p_sales.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#ffffff", margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_p_sales, use_container_width=True)
        else:
            st.caption("No inventory data found inside order json.")

with col_charts2:
    st.markdown("### 📈 Revenue Trends over Time")
    
    if df_orders.empty:
        st.info("No order history available.")
    else:
        # Format time and group
        # Live DB has created_at
        df_orders["Date"] = pd.to_datetime(df_orders["created_at"]).dt.date
        df_rev_time = df_orders.groupby("Date")["total_amount"].sum().reset_index()
        
        fig_rev = px.line(
            df_rev_time, 
            x="Date", 
            y="total_amount", 
            labels={"total_amount": "Daily Revenue (Rs.)"},
            markers=True
        )
        fig_rev.update_traces(line_color="#00ff87", marker=dict(size=8, color="#60efff"))
        fig_rev.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#ffffff", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_rev, use_container_width=True)
