import os
from jinja2 import Template
from pathlib import Path

# Base paths
base_dir = Path(__file__).resolve().parent.parent
PROMPTS_DIR = base_dir / "prompts"

def load_prompt_template(prompt_name: str, **kwargs) -> str:
    """Load and render a markdown prompt template with context variables."""
    file_path = PROMPTS_DIR / f"{prompt_name}.md"
    if not file_path.exists():
        # Try without extension
        file_path = PROMPTS_DIR / prompt_name
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt template {prompt_name} not found.")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    template = Template(content)
    return template.render(**kwargs)

def format_catalog_for_prompt(products: list) -> str:
    """Format the SQLite products table rows as a clean text list for LLM context."""
    if not products:
        return "No products available in the catalog."
        
    lines = []
    for p in products:
        # p is a dictionary or sqlite3.Row
        lines.append(f"- {p['name']} (ID: {p['id']}): Price: Rs. {p['price']} | Description: {p['description']} | Stock: {p['stock']} units")
    return "\n".join(lines)

def format_conversation_history(history: list) -> str:
    """Format conversation list for prompts."""
    lines = []
    for msg in history:
        sender_label = "Customer" if msg['sender'] == 'customer' else "Support Bot"
        lines.append(f"{sender_label}: {msg['message']}")
    return "\n".join(lines)

def inject_custom_css():
    """Inject premium CSS styling into Streamlit app for professional aesthetics."""
    import streamlit as st
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
        
        /* Base page adjustments */
        html, body, [class*="css"], .stMarkdown, p, div, label {
            font-family: 'Outfit', sans-serif !important;
        }
        
        /* Modern Premium Glass Card styles */
        .glass-card {
            background: rgba(20, 24, 33, 0.6) !important;
            border-radius: 16px !important;
            border: 1px solid rgba(255, 255, 255, 0.07) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            padding: 24px !important;
            margin-bottom: 20px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
            transition: all 0.3s ease-in-out !important;
        }
        
        .glass-card:hover {
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 12px 40px rgba(56, 189, 248, 0.05) !important;
        }
        
        .metric-title {
            font-size: 0.8rem !important;
            color: #9ca3af !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
        }
        
        .metric-value {
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            color: #ffffff !important;
            margin-top: 8px !important;
            margin-bottom: 4px !important;
            background: linear-gradient(135deg, #38bdf8 0%, #34d399 100%);
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
        }

        .metric-desc {
            font-size: 0.8rem !important;
            color: #6b7280 !important;
        }

        .pulsing-dot {
            width: 10px;
            height: 10px;
            background-color: #10b981;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
            animation: pulse 1.6s infinite;
        }

        @keyframes pulse {
            0% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
            }
            70% {
                transform: scale(1);
                box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
            }
            100% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
            }
        }

        /* Sidebar improvements */
        section[data-testid="stSidebar"] {
            background-color: #0b0f19 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            background-color: #0b0f19 !important;
        }

        /* Input styling */
        div[data-baseweb="input"] {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px !important;
        }

        div[data-baseweb="select"] {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border-radius: 8px !important;
        }

        /* Expander design */
        div[data-testid="stExpander"] {
            background-color: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 10px !important;
        }
        </style>
    """, unsafe_allow_html=True)

