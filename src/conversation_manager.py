import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.database import Database
from src.llm_provider import get_active_provider
from src.utils import load_prompt_template, format_catalog_for_prompt, format_conversation_history

class ConversationManager:
    def __init__(self):
        self.db = Database()

    def process_incoming_message(self, whatsapp_number: str, message_text: str, customer_name: str = None) -> str:
        """
        Process an incoming WhatsApp message:
        1. Get or create customer record
        2. Analyze sentiment & category
        3. Save message to DB
        4. Check business hours and auto-reply settings
        5. Generate response using active LLM
        6. Save & return response
        """
        # 1. Fetch or create customer
        customer = self.db.get_or_create_customer(whatsapp_number, customer_name)
        customer_id = customer['id']

        if customer.get('blocked') == 1:
            return "Customer is blocked. No auto-reply generated."

        # 2. Analyze intent and sentiment (fast rule-based for low latency)
        category, sentiment = self.analyze_sentiment_and_intent(message_text)

        # 3. Save customer message
        self.db.add_message(
            customer_id=customer_id,
            message=message_text,
            sender="customer",
            sentiment=sentiment,
            processed=True
        )

        # 4. Check business hours & auto-reply outside hours
        outside_hours, business_message = self.check_business_hours()
        if outside_hours:
            # Save outside-hours auto-reply to DB
            self.db.add_message(
                customer_id=customer_id,
                message=business_message,
                sender="bot",
                sentiment="neutral",
                processed=True
            )
            return business_message

        # 5. Get conversation history (last 10 messages)
        history = self.db.get_conversation_history(customer_id, limit=10)

        # If category is "order", try to extract and process the order first
        if category == "order":
            from src.order_processor import OrderProcessor
            op = OrderProcessor()
            success, result = op.process_and_save_order(customer_id)
            if success:
                # The OrderProcessor already saved the confirmation message to DB
                return result["confirmation_message"]
        
        # 6. Fetch products catalog
        products = self.db.get_all_products()
        catalog_str = format_catalog_for_prompt(products)

        # 7. Render system prompt
        business_name = self.db.get_setting("business_name") or "Pak China Traders"
        escalation_number = self.db.get_setting("escalation_number") or "+923001234567"
        
        system_prompt = load_prompt_template(
            "customer_support",
            business_name=business_name,
            escalation_number=escalation_number,
            catalog=catalog_str
        )

        # 8. Generate LLM response
        try:
            provider = get_active_provider()
            # We pass history (excluding the very last message to avoid duplication)
            history_excluding_last = history[:-1] if len(history) > 1 else []
            
            response_text = provider.get_response(
                prompt=message_text,
                conversation_history=history_excluding_last,
                system_prompt=system_prompt
            )
        except Exception as e:
            print(f"Failed to generate LLM response: {e}")
            # Fallback reply
            response_text = self.db.get_setting("default_reply_template") or "Thank you for your message. We will get back to you shortly."

        # 9. Save bot response
        self.db.add_message(
            customer_id=customer_id,
            message=response_text,
            sender="bot",
            sentiment="neutral",
            processed=True
        )

        return response_text

    def analyze_sentiment_and_intent(self, text: str) -> tuple[str, str]:
        """
        Analyze sentiment and intent category using rules.
        Returns: (category, sentiment)
        """
        text_lower = text.lower()
        
        # Sentiment detection
        sentiment = "neutral"
        negative_words = ["bad", "worst", "angry", "kharab", "bekar", "slow", "delay", "scam", "wrong", "broken", "complaint", "shikayat", "fraud", "late", "fuzool"]
        positive_words = ["good", "great", "excellent", "thanks", "thank you", "nice", "shukriya", "best", "love", "happy", "ok", "acha", "nice"]
        
        if any(word in text_lower for word in negative_words):
            sentiment = "negative"
        elif any(word in text_lower for word in positive_words):
            sentiment = "positive"
            
        # Category detection
        category = "inquiry"
        order_words = ["buy", "order", "book", "kharid", "chahye", "purchase", "price of", "cost of", "rate", "lelo", "mangwana"]
        complaint_words = ["complaint", "shikayat", "delay", "wrong", "broken", "damage", "refund", "return", "miss", "not received", "fuzool"]
        
        if any(word in text_lower for word in complaint_words):
            category = "complaint"
        elif any(word in text_lower for word in order_words):
            category = "order"
            
        return category, sentiment

    def check_business_hours(self) -> tuple[bool, str]:
        """
        Check if current time is outside business hours.
        Returns: (is_outside_hours, auto_reply_message)
        """
        auto_reply_enabled = self.db.get_setting("auto_reply_outside_hours") == "1"
        if not auto_reply_enabled:
            return False, ""

        start_time_str = self.db.get_setting("business_hours_start") or "09:00"
        end_time_str = self.db.get_setting("business_hours_end") or "18:00"

        try:
            now = datetime.now().time()
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            is_outside = False
            if start_time <= end_time:
                # Normal hours, e.g., 9 AM to 6 PM
                if now < start_time or now > end_time:
                    is_outside = True
            else:
                # Overnight hours, e.g., 9 PM to 6 AM
                if now < start_time and now > end_time:
                    is_outside = True

            if is_outside:
                business_name = self.db.get_setting("business_name") or "Pak China Traders"
                msg = f"Thank you for contacting {business_name}. We are currently closed. Our business hours are {start_time_str} to {end_time_str}. We will respond as soon as we open!"
                return True, msg
        except Exception as e:
            print(f"Error checking business hours: {e}")

        return False, ""
