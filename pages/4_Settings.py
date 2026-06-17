import streamlit as st
import sys
import shutil
import pandas as pd
from pathlib import Path
from datetime import datetime


# Add root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.database import Database
from src.llm_provider import LLMProvider, get_active_provider
from src.utils import inject_custom_css

st.set_page_config(
    page_title="Settings - Pak China Traders",
    page_icon="⚙️",
    layout="wide"
)

inject_custom_css()

db = Database()

# Page Title
st.markdown("""
<div style='margin-bottom: 25px;'>
    <h1 style='margin: 0; font-size: 2.2rem; font-weight: 800; color: #ffffff;'>
        ⚙️ Settings & Core Configuration
    </h1>
    <p style='margin: 5px 0 0 0; color: #9ca3af; font-size: 1rem;'>
        Live settings update in real-time. No application restarts required.
    </p>
</div>
""", unsafe_allow_html=True)

# Main Form Actions
tab_llm, tab_whatsapp, tab_business, tab_catalog, tab_danger = st.tabs([
    "🤖 LLM Provider", 
    "💬 WhatsApp Channel", 
    "💼 Business Rules", 
    "📦 Product Catalog",
    "⚠️ Danger Zone"
])

# ----------------- TAB: LLM PROVIDER -----------------
with tab_llm:
    st.subheader("LLM Engine Tuning")
    
    current_provider = db.get_setting("llm_provider") or "Gemini"
    
    provider_sel = st.selectbox(
        "Select Active LLM Provider",
        options=["Gemini", "OpenAI", "Claude", "DeepSeek"],
        index=["Gemini", "OpenAI", "Claude", "DeepSeek"].index(current_provider)
    )
    
    # Load API keys and configurations
    openai_key = db.get_setting("openai_api_key", decrypt=True)
    openai_mod = db.get_setting("openai_model") or "gpt-4o-mini"
    
    claude_key = db.get_setting("claude_api_key", decrypt=True)
    claude_mod = db.get_setting("claude_model") or "claude-3-5-sonnet-20240620"
    
    gemini_key = db.get_setting("gemini_api_key", decrypt=True)
    gemini_mod = db.get_setting("gemini_model") or "gemini-1.5-flash"
    
    deepseek_key = db.get_setting("deepseek_api_key", decrypt=True)
    deepseek_mod = db.get_setting("deepseek_model") or "deepseek-chat"
    
    temp_val = float(db.get_setting("temperature") or "0.3")
    max_tok = int(db.get_setting("max_tokens") or "500")
    sys_prompt = db.get_setting("system_prompt") or ""

    st.write("---")
    
    # Render fields based on selection
    if provider_sel == "OpenAI":
        selected_key = st.text_input("OpenAI API Key", value=openai_key, type="password")
        selected_model = st.selectbox("Model Selection", options=LLMProvider.get_available_models("OpenAI"), index=LLMProvider.get_available_models("OpenAI").index(openai_mod) if openai_mod in LLMProvider.get_available_models("OpenAI") else 0)
    elif provider_sel == "Claude":
        selected_key = st.text_input("Claude (Anthropic) API Key", value=claude_key, type="password")
        selected_model = st.selectbox("Model Selection", options=LLMProvider.get_available_models("Claude"), index=LLMProvider.get_available_models("Claude").index(claude_mod) if claude_mod in LLMProvider.get_available_models("Claude") else 0)
    elif provider_sel == "Gemini":
        selected_key = st.text_input("Gemini API Key", value=gemini_key, type="password")
        selected_model = st.selectbox("Model Selection", options=LLMProvider.get_available_models("Gemini"), index=LLMProvider.get_available_models("Gemini").index(gemini_mod) if gemini_mod in LLMProvider.get_available_models("Gemini") else 0)
    else:  # DeepSeek
        selected_key = st.text_input("DeepSeek API Key", value=deepseek_key, type="password")
        selected_model = st.selectbox("Model Selection", options=LLMProvider.get_available_models("DeepSeek"), index=LLMProvider.get_available_models("DeepSeek").index(deepseek_mod) if deepseek_mod in LLMProvider.get_available_models("DeepSeek") else 0)

    temperature = st.slider("Temperature (Creativity Control)", min_value=0.0, max_value=1.0, value=temp_val, step=0.05)
    max_tokens = st.number_input("Max Output Tokens", min_value=50, max_value=4000, value=max_tok, step=50)
    
    system_prompt = st.text_area("System Prompt (Instructions Template)", value=sys_prompt, height=200)

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("💾 Save LLM Configuration", use_container_width=True):
            # Save selection
            db.save_setting("llm_provider", provider_sel)
            
            # Save keys and models for the chosen provider
            if provider_sel == "OpenAI":
                db.save_setting("openai_api_key", selected_key, "OpenAI")
                db.save_setting("openai_model", selected_model, "OpenAI")
            elif provider_sel == "Claude":
                db.save_setting("claude_api_key", selected_key, "Claude")
                db.save_setting("claude_model", selected_model, "Claude")
            elif provider_sel == "Gemini":
                db.save_setting("gemini_api_key", selected_key, "Gemini")
                db.save_setting("gemini_model", selected_model, "Gemini")
            elif provider_sel == "DeepSeek":
                db.save_setting("deepseek_api_key", selected_key, "DeepSeek")
                db.save_setting("deepseek_model", selected_model, "DeepSeek")
                
            db.save_setting("temperature", str(temperature))
            db.save_setting("max_tokens", str(max_tokens))
            db.save_setting("system_prompt", system_prompt)
            
            st.success("LLM engine configurations updated successfully! Settings are live.")
            st.rerun()
            
    with btn_col2:
        if st.button("🧪 Test Selected Key", use_container_width=True):
            if not selected_key:
                st.warning("Please input an API key first to run tests.")
            else:
                with st.spinner("Testing API connection..."):
                    test_prov = LLMProvider(
                        provider_name=provider_sel,
                        api_key=selected_key,
                        model_name=selected_model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    is_valid = test_prov.validate_api_key()
                    if is_valid:
                        st.success(f"Connection test SUCCESSFUL! {provider_sel} key is verified and operational.")
                    else:
                        st.error(f"Connection test FAILED. Please check if your {provider_sel} API key is correct and possesses model access permissions.")

# ----------------- TAB: WHATSAPP SETTINGS -----------------
with tab_whatsapp:
    st.subheader("Twilio Integration Config")
    
    # Webhook Display
    st.info("💡 **Webhook Configuration:** Use the URLs below as the Webhook URLs in your Twilio Sandbox or Phone Number settings console.")
    st.text_input("WhatsApp Webhook Endpoint URL (Copy this)", value=f"{db.get_setting('webhook_url') or 'http://localhost:8000'}/webhooks/whatsapp", disabled=True)
    st.text_input("Voice Webhook Endpoint URL (Copy this)", value=f"{db.get_setting('webhook_url') or 'http://localhost:8000'}/webhooks/voice", disabled=True)
    
    st.write("---")
    
    # Twilio creds inputs
    twilio_sid = db.get_setting("twilio_account_sid")
    twilio_tok = db.get_setting("twilio_auth_token", decrypt=True)
    twilio_num = db.get_setting("twilio_phone_number") or "whatsapp:+14155238886"
    twilio_voice = db.get_setting("twilio_voice_number") or ""
    
    new_sid = st.text_input("Twilio Account SID", value=twilio_sid)
    new_token = st.text_input("Twilio Auth Token", value=twilio_tok, type="password")
    new_phone = st.text_input("WhatsApp Sandbox/Sender Phone Number", value=twilio_num, placeholder="whatsapp:+14155238886")
    new_voice = st.text_input("Twilio Inbound Voice Caller Number", value=twilio_voice, placeholder="+1234567890")
    
    if st.button("💾 Save Twilio Configuration"):
        db.save_setting("twilio_account_sid", new_sid)
        db.save_setting("twilio_auth_token", new_token)
        db.save_setting("twilio_phone_number", new_phone)
        db.save_setting("twilio_voice_number", new_voice)
        st.success("WhatsApp channel parameters updated successfully!")
        st.rerun()

# ----------------- TAB: BUSINESS SETTINGS -----------------
with tab_business:
    st.subheader("Business Rules & Auto-replies")
    
    b_name = st.text_input("Business Name", value=db.get_setting("business_name") or "Pak China Traders")
    b_start = st.text_input("Business Hours Start (24h format)", value=db.get_setting("business_hours_start") or "09:00", max_chars=5)
    b_end = st.text_input("Business Hours End (24h format)", value=db.get_setting("business_hours_end") or "18:00", max_chars=5)
    
    auto_reply = st.checkbox("Enable Automated Outside-Hours Message", value=db.get_setting("auto_reply_outside_hours") == "1")
    
    b_template = st.text_area("Default Fallback Auto-Reply Template (Used if APIs timeout)", value=db.get_setting("default_reply_template") or "", height=80)
    escalation_num = st.text_input("Human Support Escalation WhatsApp/Phone Number", value=db.get_setting("escalation_number") or "+923001234567")

    if st.button("💾 Save Business Rules"):
        db.save_setting("business_name", b_name)
        db.save_setting("business_hours_start", b_start)
        db.save_setting("business_hours_end", b_end)
        db.save_setting("auto_reply_outside_hours", "1" if auto_reply else "0")
        db.save_setting("default_reply_template", b_template)
        db.save_setting("escalation_number", escalation_num)
        st.success("Business rules saved successfully!")
        st.rerun()

# ----------------- TAB: PRODUCT CATALOG -----------------
with tab_catalog:
    st.subheader("Manage Product Inventory Catalog")
    st.caption("These products are queried by the order extraction engine to match prices, quantities, and verify availability.")
    
    # Display current catalog
    products = db.get_all_products()
    if products:
        st.markdown("### 🛒 Active Inventory Catalog")
        cat_df = []
        for p in products:
            cat_df.append({
                "Product ID": p["id"],
                "Item Name": p["name"],
                "Unit Price": f"Rs. {p['price']:,.2f}",
                "Description": p["description"],
                "Stock": p["stock"]
            })
        st.table(pd.DataFrame(cat_df))
    else:
        st.info("Product catalog is empty. Add item below.")

    st.write("---")
    
    # Add new product form
    st.markdown("### ➕ Add Product to Catalog")
    new_p_name = st.text_input("Product Name", placeholder="e.g. Silk Thread Roll")
    new_p_price = st.number_input("Unit Price (Rs.)", min_value=0.0, step=10.0, value=0.0)
    new_p_desc = st.text_input("Short Description", placeholder="Description of fabric material, origin...")
    new_p_stock = st.number_input("Available Stock Quantity", min_value=0, step=10, value=100)
    
    if st.button("➕ Add Item"):
        if not new_p_name.strip() or new_p_price <= 0:
            st.warning("Please supply a valid Product Name and a Unit Price greater than zero.")
        else:
            success = db.add_product(new_p_name, new_p_price, new_p_desc, new_p_stock)
            if success:
                st.success(f"Product '{new_p_name}' successfully added to database catalog!")
                st.rerun()
            else:
                st.error("Integrity error. Product name might already exist in catalog.")

# ----------------- TAB: DANGER ZONE -----------------
with tab_danger:
    st.subheader("Database Operations & Safe Backups")
    
    # Backup Database
    if st.button("💾 Backup SQLite Database"):
        try:
            db_file = Path(db.db_path)
            backup_file = db_file.parent / f"{db_file.name}.bak"
            shutil.copy(str(db_file), str(backup_file))
            st.success(f"Database backed up successfully to `{backup_file.name}`!")
        except Exception as e:
            st.error(f"Failed to create backup: {e}")

    # Clear Conversation Logs
    if st.button("🧹 Clear Chat Conversations Only", help="Removes messages history. Customers & Orders are preserved."):
        db.clear_conversations()
        st.warning("All customer message logs deleted successfully from conversations database!")
        st.rerun()

    st.write("---")
    st.markdown("<h3 style='color:#ef4444;'>🚨 System Destructive Resets</h3>", unsafe_allow_html=True)
    
    # Full Reset
    if st.button("🔥 Hard Reset Database (Delete All Data)", help="Resets settings, catalog, order records, and logs back to defaults."):
        db.reset_all_data()
        st.error("Entire database has been completely wiped and seeded back to fresh defaults! Streamlit sessions reloaded.")
        st.rerun()
