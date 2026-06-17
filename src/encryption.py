import sys
from pathlib import Path
from cryptography.fernet import Fernet

# Add parent directory to sys.path to resolve imports correctly
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import ENCRYPTION_KEY

def encrypt_value(value: str) -> str:
    """Encrypt a string value using Fernet symmetric encryption."""
    if not value:
        return ""
    try:
        cipher = Fernet(ENCRYPTION_KEY)
        return cipher.encrypt(value.encode()).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return value

def decrypt_value(encrypted_value: str) -> str:
    """Decrypt a Fernet encrypted string, falling back to original if decryption fails."""
    if not encrypted_value:
        return ""
    try:
        cipher = Fernet(ENCRYPTION_KEY)
        return cipher.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        # If decryption fails, the value might be plain-text or invalid key, return as-is
        return encrypted_value
