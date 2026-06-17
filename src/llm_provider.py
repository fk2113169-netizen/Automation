import sys
from pathlib import Path
import litellm

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.database import Database

# Pricing details per 1 Million tokens (Input, Output) in USD
PRICING_TABLE = {
    # OpenAI
    "gpt-4o": (5.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    # Claude (Anthropic)
    "claude-3-5-sonnet-20240620": (3.00, 15.00),
    "claude-3-opus-20240229": (15.00, 75.00),
    "claude-3-haiku-20240307": (0.25, 1.25),
    # Gemini
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
    # DeepSeek
    "deepseek-chat": (0.20, 0.28),
}

# Map simple provider names to LiteLLM prefixes
LITELLM_MODEL_PREFIX = {
    "OpenAI": "",
    "Claude": "anthropic/",
    "Gemini": "gemini/",
    "DeepSeek": "deepseek/",
}

class LLMProvider:
    def __init__(self, provider_name: str, api_key: str, model_name: str, temperature: float = 0.3, max_tokens: int = 500):
        self.provider_name = provider_name
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.db = Database()

    def get_litellm_model_name(self) -> str:
        prefix = LITELLM_MODEL_PREFIX.get(self.provider_name, "")
        # Remove any existing prefix if it already matches
        model = self.model_name
        if "/" in model:
            return model
        return f"{prefix}{model}"

    def get_response(self, prompt: str, conversation_history: list = None, system_prompt: str = None) -> str:
        """
        Generate response from LLM, tracking token counts and api costs.
        conversation_history: list of dicts with {"sender": "customer"/"bot", "message": "..."}
        """
        if not self.api_key:
            return "Error: LLM API key not configured. Please go to settings and add your API key."

        # Set up messages list
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        if conversation_history:
            for chat in conversation_history:
                role = "user" if chat.get("sender") == "customer" else "assistant"
                messages.append({"role": role, "content": chat.get("message", "")})
                
        # Add current user prompt
        messages.append({"role": "user", "content": prompt})

        # Run completion using litellm
        litellm_model = self.get_litellm_model_name()
        
        # Configure litellm params
        litellm_kwargs = {
            "model": litellm_model,
            "messages": messages,
            "api_key": self.api_key,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # Custom base URL for DeepSeek if needed
        if self.provider_name == "DeepSeek":
            litellm_kwargs["api_base"] = "https://api.deepseek.com"

        try:
            # Disable warning logs from LiteLLM
            litellm.set_verbose = False
            
            response = litellm.completion(**litellm_kwargs)
            
            response_text = response.choices[0].message.content
            
            # Extract usage and calculate cost
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            cost = self.calculate_cost(prompt_tokens, completion_tokens)
            
            # Log usage in the database
            self.db.log_llm_usage(
                provider=self.provider_name,
                model=self.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost
            )
            
            return response_text
        except Exception as e:
            print(f"LLM API Error for {self.provider_name} ({self.model_name}): {e}")
            return f"Error connecting to LLM provider ({self.provider_name}): {str(e)}"

    def validate_api_key(self) -> bool:
        """Validate API key by performing a lightweight 1-token query."""
        if not self.api_key:
            return False
            
        litellm_model = self.get_litellm_model_name()
        
        litellm_kwargs = {
            "model": litellm_model,
            "messages": [{"role": "user", "content": "test"}],
            "api_key": self.api_key,
            "max_tokens": 1,
        }
        
        if self.provider_name == "DeepSeek":
            litellm_kwargs["api_base"] = "https://api.deepseek.com"
            
        try:
            litellm.completion(**litellm_kwargs)
            return True
        except Exception as e:
            print(f"API key validation failed: {e}")
            return False

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate LLM call cost in USD."""
        rates = PRICING_TABLE.get(self.model_name)
        if not rates:
            # Try searching by prefix/substring
            rates = (0.50, 1.50)  # Default rate: $0.50/M input, $1.50/M output
            for model_key, rate in PRICING_TABLE.items():
                if model_key in self.model_name:
                    rates = rate
                    break
        
        input_cost = (prompt_tokens / 1_000_000.0) * rates[0]
        output_cost = (completion_tokens / 1_000_000.0) * rates[1]
        return input_cost + output_cost

    @staticmethod
    def get_available_models(provider_name: str) -> list:
        """Return available models for a given provider."""
        models = {
            "OpenAI": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            "Claude": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            "Gemini": ["gemini-1.5-flash", "gemini-1.5-pro"],
            "DeepSeek": ["deepseek-chat"]
        }
        return models.get(provider_name, [])


def get_active_provider() -> LLMProvider:
    """Factory function to build and return an LLMProvider using settings from the Database."""
    db = Database()
    
    # Get configuration
    provider = db.get_setting("llm_provider") or "Gemini"
    
    # Map provider to get key and model
    api_key_setting_map = {
        "OpenAI": "openai_api_key",
        "Claude": "claude_api_key",
        "Gemini": "gemini_api_key",
        "DeepSeek": "deepseek_api_key"
    }
    
    model_setting_map = {
        "OpenAI": "openai_model",
        "Claude": "claude_model",
        "Gemini": "gemini_model",
        "DeepSeek": "deepseek_model"
    }
    
    api_key = db.get_setting(api_key_setting_map.get(provider, "gemini_api_key"), decrypt=True)
    model = db.get_setting(model_setting_map.get(provider, "gemini_model"))
    
    # If no model configured, fallback to standard defaults
    if not model:
        defaults = {
            "OpenAI": "gpt-4o-mini",
            "Claude": "claude-3-5-sonnet-20240620",
            "Gemini": "gemini-1.5-flash",
            "DeepSeek": "deepseek-chat"
        }
        model = defaults.get(provider, "gemini-1.5-flash")
        
    temp_str = db.get_setting("temperature") or "0.3"
    max_tokens_str = db.get_setting("max_tokens") or "500"
    
    try:
        temp = float(temp_str)
    except ValueError:
        temp = 0.3
        
    try:
        max_tokens = int(max_tokens_str)
    except ValueError:
        max_tokens = 500
        
    return LLMProvider(
        provider_name=provider,
        api_key=api_key,
        model_name=model,
        temperature=temp,
        max_tokens=max_tokens
    )
