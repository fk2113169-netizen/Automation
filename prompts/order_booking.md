Extract order details from the conversation. 
Evaluate carefully if the customer is placing an order, and extract the details.

Product Catalog Reference:
{{ catalog }}

You must return a valid JSON object ONLY. Do not include markdown code block formatting like ```json or any explanation outside the JSON.

JSON Schema:
{
  "products": [
    {
      "name": "Product name from the catalog or as specified by the customer",
      "quantity": 1,
      "unit_price": 0.0
    }
  ],
  "customer_address": "Full shipping address (leave empty if not mentioned)",
  "delivery_date": "Requested delivery date (leave empty if not mentioned)",
  "special_notes": "Any special instructions or comments from customer",
  "confidence": 0.0 to 1.0 (float reflecting how complete the order information is)
}

If critical details (like product name or quantity) are missing or ambiguous, keep "confidence" low (< 0.5) so we can ask clarifying questions.

Conversation transcript to extract from:
{{ conversation }}
