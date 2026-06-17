import json
import re
import sys
from pathlib import Path

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.database import Database
from src.llm_provider import get_active_provider
from src.utils import load_prompt_template, format_catalog_for_prompt, format_conversation_history

class OrderProcessor:
    def __init__(self):
        self.db = Database()

    def extract_order_from_conversation(self, customer_id: str) -> dict:
        """
        Use the active LLM to extract order details from conversation history.
        Returns a parsed dictionary of order details.
        """
        # Fetch conversation history (last 10 messages)
        history = self.db.get_conversation_history(customer_id, limit=10)
        history_str = format_conversation_history(history)

        # Fetch products
        products = self.db.get_all_products()
        catalog_str = format_catalog_for_prompt(products)

        # Render prompt
        prompt = load_prompt_template(
            "order_booking",
            catalog=catalog_str,
            conversation=history_str
        )

        try:
            # Call active LLM
            provider = get_active_provider()
            # We call LLM directly with the prompt (system instructions are already inside the template)
            response_raw = provider.get_response(prompt=prompt, conversation_history=[], system_prompt="You are a strict data extraction parser. Output JSON only.")
            
            # Extract JSON block using regex (to handle markdown code blocks or text wrappers gracefully)
            json_match = re.search(r"(\{.*\})", response_raw, re.DOTALL)
            if json_match:
                parsed_json = json.loads(json_match.group(1))
            else:
                parsed_json = json.loads(response_raw)
                
            return parsed_json
        except Exception as e:
            print(f"Error extracting order from LLM: {e}")
            return {
                "products": [],
                "customer_address": "",
                "delivery_date": "",
                "special_notes": f"Error during extraction: {str(e)}",
                "confidence": 0.0
            }

    def process_and_save_order(self, customer_id: str) -> tuple[bool, dict]:
        """
        Extract order, validate products against actual catalog database, and save if confidence is high.
        Returns (success, result_dict)
        """
        extracted = self.extract_order_from_conversation(customer_id)
        confidence = extracted.get("confidence", 0.0)
        
        if confidence < 0.7 or not extracted.get("products"):
            return False, {
                "message": "Order information is incomplete. Need more details from the customer.",
                "extracted_details": extracted
            }

        # Validate products against catalog and calculate total price
        db_products = self.db.get_all_products()
        validated_products = []
        total_amount = 0.0

        for ep in extracted["products"]:
            ep_name = ep.get("name", "").lower()
            qty = int(ep.get("quantity", 0))
            if qty <= 0:
                continue

            # Look for matches in db
            matched_product = None
            for db_p in db_products:
                if db_p["name"].lower() in ep_name or ep_name in db_p["name"].lower():
                    matched_product = db_p
                    break

            if matched_product:
                price = matched_product["price"]
                product_total = price * qty
                total_amount += product_total
                validated_products.append({
                    "product_id": matched_product["id"],
                    "name": matched_product["name"],
                    "quantity": qty,
                    "unit_price": price,
                    "total_price": product_total
                })
            else:
                # Fallback to LLM parsed price if product not found in catalog database
                price = float(ep.get("unit_price", 0.0))
                product_total = price * qty
                total_amount += product_total
                validated_products.append({
                    "product_id": "unknown",
                    "name": ep.get("name"),
                    "quantity": qty,
                    "unit_price": price,
                    "total_price": product_total
                })

        if not validated_products:
            return False, {
                "message": "No valid products could be matched to the catalog.",
                "extracted_details": extracted
            }

        order_json = {
            "products": validated_products,
            "customer_address": extracted.get("customer_address", ""),
            "delivery_date": extracted.get("delivery_date", ""),
            "special_notes": extracted.get("special_notes", "")
        }

        # Save order to DB
        order_id = self.db.create_order(
            customer_id=customer_id,
            order_json=order_json,
            total_amount=total_amount,
            status="pending"
        )
        
        # Generate tracking and payment link simulation (as requested)
        order_json["order_id"] = order_id
        order_json["total_amount"] = total_amount
        order_json["status"] = "pending"
        order_json["payment_link"] = f"https://jazzcash.com.pk/pay?order={order_id}&amount={total_amount}"
        order_json["tracking_link"] = f"https://pakchinatraders.com/track/{order_id}"

        # Send confirmation message to customer (simulate or save bot message)
        confirm_msg = (
            f"📦 *Order Booked Successfully!*\n\n"
            f"Order ID: `{order_id}`\n"
            f"Total Amount: Rs. {total_amount:,.2f}\n"
            f"Items:\n" + "\n".join([f"- {item['name']} x {item['quantity']}" for item in validated_products]) + "\n\n"
            f"Address: {order_json['customer_address']}\n"
            f"Payment Link (JazzCash): {order_json['payment_link']}\n"
            f"Track Order: {order_json['tracking_link']}"
        )
        
        self.db.add_message(
            customer_id=customer_id,
            message=confirm_msg,
            sender="bot",
            sentiment="positive",
            processed=True
        )

        return True, {
            "order_id": order_id,
            "total_amount": total_amount,
            "details": order_json,
            "confirmation_message": confirm_msg
        }
