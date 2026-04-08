import pyotp
import time

def generate_code(secret: str) -> str:
    """Enter the key to generate a 6-digit verification code"""
    # Clean spaces in the key
    clean_secret = secret.replace(" ", "").upper()
    return pyotp.TOTP(clean_secret).now()

def get_remaining_seconds() -> int:
    """Calculate the remaining seconds for the current period."""
    return 30 - int(time.time()) % 30