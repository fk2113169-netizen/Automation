import sqlite3
import json
import uuid
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import DATABASE_PATH
from src.encryption import encrypt_value, decrypt_value

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_db()

    def get_connection(self):
        """Get a sqlite connection. Use short-lived connections to prevent locking."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Create tables if they do not exist and seed default settings."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Customers Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                whatsapp_number TEXT UNIQUE,
                name TEXT,
                first_contact TIMESTAMP,
                total_orders INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0.0,
                blocked INTEGER DEFAULT 0
            )
            """)
            
            # 2. Conversations Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                customer_id TEXT,
                message TEXT,
                sender TEXT CHECK(sender IN ('customer', 'bot')),
                timestamp TIMESTAMP,
                processed INTEGER DEFAULT 0,
                sentiment TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
            """)
            
            # 3. Orders Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer_id TEXT,
                order_json TEXT,
                status TEXT CHECK(status IN ('pending', 'confirmed', 'shipped', 'delivered')),
                total_amount REAL,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
            """)
            
            # 4. Settings Table (For live system configuration, sensitive keys encrypted)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                provider TEXT,
                updated_at TIMESTAMP
            )
            """)
            
            # 5. Calls Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id TEXT PRIMARY KEY,
                customer_id TEXT,
                duration INTEGER,
                transcription TEXT,
                recording_url TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
            """)

            # 6. Products Catalog Table (Useful for dynamic catalogs)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE,
                price REAL,
                description TEXT,
                stock INTEGER DEFAULT 100
            )
            """)

            # 7. LLM Usage Table for tracking costs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_usage (
                id TEXT PRIMARY KEY,
                provider TEXT,
                model TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                cost REAL,
                timestamp TIMESTAMP
            )
            """)
            
            conn.commit()

        # Seed defaults
        self._seed_default_settings()
        self._seed_default_products()

    def _seed_default_settings(self):
        """Seed default settings if they do not exist."""
        defaults = [
            ("llm_provider", "Gemini", "system"),
            ("openai_api_key", "", "OpenAI"),
            ("openai_model", "gpt-4o-mini", "OpenAI"),
            ("claude_api_key", "", "Claude"),
            ("claude_model", "claude-3-5-sonnet-20240620", "Claude"),
            ("gemini_api_key", "", "Gemini"),
            ("gemini_model", "gemini-1.5-flash", "Gemini"),
            ("deepseek_api_key", "", "DeepSeek"),
            ("deepseek_model", "deepseek-chat", "DeepSeek"),
            ("temperature", "0.3", "system"),
            ("max_tokens", "500", "system"),
            ("system_prompt", "You are a friendly WhatsApp customer support bot for Pak China Traders.\n- Be polite, concise, and professional\n- If asked about products, check our catalog (provided below)\n- Speak Urdu/English naturally\n- If customer mentions an order, ask for order ID\n- Escalate to human if customer is angry or complex issue\n- Keep responses under 2 WhatsApp messages", "system"),
            ("business_name", "Pak China Traders", "system"),
            ("business_hours_start", "09:00", "system"),
            ("business_hours_end", "18:00", "system"),
            ("escalation_number", "+923001234567", "system"),
            ("default_reply_template", "Thank you for contacting Pak China Traders. Our representative will get back to you shortly.", "system"),
            ("auto_reply_outside_hours", "1", "system") # 1 = True, 0 = False
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for key, val, provider in defaults:
                cursor.execute("SELECT key FROM settings WHERE key = ?", (key,))
                if not cursor.fetchone():
                    # Encrypt API keys
                    if "api_key" in key and val != "":
                        encrypted_val = encrypt_value(val)
                    else:
                        encrypted_val = val
                    cursor.execute(
                        "INSERT INTO settings (key, value, provider, updated_at) VALUES (?, ?, ?, ?)",
                        (key, encrypted_val, provider, datetime.now().isoformat())
                    )
            conn.commit()

    def _seed_default_products(self):
        """Seed a few products into the catalog if empty."""
        default_products = [
            ("P1", "Silk Thread", 450.0, "High-quality embroidery silk thread imported from China.", 500),
            ("P2", "Polyester Fabric", 1200.0, "Durable polyester fabric rolls, direct from Shanghai.", 150),
            ("P3", "Sewing Machine Kit", 18500.0, "Heavy-duty electric sewing machine with Chinese parts.", 30),
            ("P4", "Cotton Knitted Yarn", 800.0, "Soft combed cotton yarn for textile manufacturing.", 250),
            ("P5", "Industrial Sewing Needles", 350.0, "Pack of 10 steel sewing needles for industrial use.", 1000)
        ]
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                for pid, name, price, desc, stock in default_products:
                    cursor.execute(
                        "INSERT INTO products (id, name, price, description, stock) VALUES (?, ?, ?, ?, ?)",
                        (pid, name, price, desc, stock)
                    )
                conn.commit()

    # Settings Accessors
    def get_setting(self, key: str, decrypt: bool = False) -> str:
        """Retrieve a setting value, optionally decrypting it."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                val = row[0]
                if decrypt and "api_key" in key:
                    return decrypt_value(val)
                return val
            return ""

    def save_setting(self, key: str, value: str, provider: str = "system") -> bool:
        """Save a setting value, encrypting it if it's an API key."""
        if "api_key" in key:
            value_to_save = encrypt_value(value)
        else:
            value_to_save = value

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value, provider, updated_at) VALUES (?, ?, ?, ?)",
                (key, value_to_save, provider, datetime.now().isoformat())
            )
            conn.commit()
            return True

    # Customer Management
    def get_or_create_customer(self, whatsapp_number: str, name: str = None) -> dict:
        """Retrieve a customer by number, or create if not exists."""
        # Standardize number
        whatsapp_number = whatsapp_number.strip().replace(" ", "")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE whatsapp_number = ?", (whatsapp_number,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            
            # Create customer
            customer_id = str(uuid.uuid4())
            customer_name = name if name else f"Customer {whatsapp_number[-4:]}"
            now_str = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO customers (id, whatsapp_number, name, first_contact, total_orders, total_spent, blocked) VALUES (?, ?, ?, ?, 0, 0.0, 0)",
                (customer_id, whatsapp_number, customer_name, now_str)
            )
            conn.commit()
            
            return {
                "id": customer_id,
                "whatsapp_number": whatsapp_number,
                "name": customer_name,
                "first_contact": now_str,
                "total_orders": 0,
                "total_spent": 0.0,
                "blocked": 0
            }

    def get_customer(self, customer_id: str) -> dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_all_customers(self) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers ORDER BY first_contact DESC")
            return [dict(row) for row in cursor.fetchall()]

    def update_customer_block_status(self, customer_id: str, blocked: bool) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE customers SET blocked = ? WHERE id = ?", (1 if blocked else 0, customer_id))
            conn.commit()
            return True

    # Conversation Management
    def add_message(self, customer_id: str, message: str, sender: str, sentiment: str = "neutral", processed: bool = True) -> dict:
        msg_id = str(uuid.uuid4())
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (id, customer_id, message, sender, timestamp, processed, sentiment) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (msg_id, customer_id, message, sender, now_str, 1 if processed else 0, sentiment)
            )
            conn.commit()
        return {
            "id": msg_id,
            "customer_id": customer_id,
            "message": message,
            "sender": sender,
            "timestamp": now_str,
            "processed": processed,
            "sentiment": sentiment
        }

    def get_conversation_history(self, customer_id: str, limit: int = 10) -> list:
        """Get recent conversation messages for a customer, in chronological order."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM conversations WHERE customer_id = ? ORDER BY timestamp DESC LIMIT ?",
                (customer_id, limit)
            )
            rows = cursor.fetchall()
            # Reverse to get chronological order (oldest to newest)
            return [dict(row) for row in reversed(rows)]

    # Product/Catalog Management
    def get_all_products(self) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]

    def add_product(self, name: str, price: float, description: str, stock: int = 100) -> bool:
        pid = str(uuid.uuid4())
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO products (id, name, price, description, stock) VALUES (?, ?, ?, ?, ?)",
                    (pid, name, price, description, stock)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def update_product(self, pid: str, name: str, price: float, description: str, stock: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET name = ?, price = ?, description = ?, stock = ? WHERE id = ?",
                (name, price, description, stock, pid)
            )
            conn.commit()
            return True

    def delete_product(self, pid: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (pid,))
            conn.commit()
            return True

    # Order Management
    def create_order(self, customer_id: str, order_json: dict, total_amount: float, status: str = "pending") -> str:
        order_id = str(uuid.uuid4())
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Insert order
            cursor.execute(
                "INSERT INTO orders (id, customer_id, order_json, status, total_amount, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (order_id, customer_id, json.dumps(order_json), status, total_amount, now_str, now_str)
            )
            # Update customer statistics
            cursor.execute(
                "UPDATE customers SET total_orders = total_orders + 1, total_spent = total_spent + ? WHERE id = ?",
                (total_amount, customer_id)
            )
            conn.commit()
        return order_id

    def get_all_orders(self) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.*, c.name as customer_name, c.whatsapp_number as customer_phone 
                FROM orders o 
                JOIN customers c ON o.customer_id = c.id 
                ORDER BY o.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def update_order_status(self, order_id: str, status: str) -> bool:
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                (status, now_str, order_id)
            )
            conn.commit()
            return True

    # Call Logging
    def log_call(self, customer_id: str, duration: int, transcription: str, recording_url: str = "") -> str:
        call_id = str(uuid.uuid4())
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO calls (id, customer_id, duration, transcription, recording_url, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (call_id, customer_id, duration, transcription, recording_url, now_str)
            )
            conn.commit()
        return call_id

    def get_all_calls(self) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ca.*, cu.name as customer_name, cu.whatsapp_number as customer_phone 
                FROM calls ca 
                JOIN customers cu ON ca.customer_id = cu.id 
                ORDER BY ca.timestamp DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    # LLM Cost Tracking
    def log_llm_usage(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int, cost: float) -> str:
        usage_id = str(uuid.uuid4())
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO llm_usage (id, provider, model, prompt_tokens, completion_tokens, cost, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (usage_id, provider, model, prompt_tokens, completion_tokens, cost, now_str)
            )
            conn.commit()
        return usage_id

    def get_llm_costs_by_provider(self) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT provider, SUM(prompt_tokens) as total_prompt_tokens, 
                       SUM(completion_tokens) as total_completion_tokens, 
                       SUM(cost) as total_cost, COUNT(*) as total_requests
                FROM llm_usage 
                GROUP BY provider
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_total_llm_cost(self) -> float:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(cost) FROM llm_usage")
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else 0.0

    # Clear/Reset Utils
    def reset_all_data(self) -> bool:
        """Delete tables and re-initialize."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS conversations")
            cursor.execute("DROP TABLE IF EXISTS orders")
            cursor.execute("DROP TABLE IF EXISTS calls")
            cursor.execute("DROP TABLE IF EXISTS customers")
            cursor.execute("DROP TABLE IF EXISTS settings")
            cursor.execute("DROP TABLE IF EXISTS products")
            cursor.execute("DROP TABLE IF EXISTS llm_usage")
            conn.commit()
        self.init_db()
        return True

    def clear_conversations(self) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations")
            conn.commit()
        return True

