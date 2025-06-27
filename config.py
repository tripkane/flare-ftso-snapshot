
"""
Configuration module for FTSO snapshot application.
"""
from typing import Optional, List
from dotenv import load_dotenv
import os

load_dotenv()

# Email configuration
SENDER_EMAIL: Optional[str] = os.getenv("SENDER_EMAIL")
EMAIL_USER: Optional[str] = os.getenv("EMAIL_USER")
EMAIL_PASS: Optional[str] = os.getenv("EMAIL_PASS")
RECIPIENTS: List[Optional[str]] = [os.getenv("RECIPIENT_1"), os.getenv("RECIPIENT_2")]

# RPC configuration
FLARE_RPC_URL: str = os.getenv("FLARE_RPC_URL", "https://flare-api.flare.network/ext/C/rpc")
SONGBIRD_RPC_URL: str = os.getenv("SONGBIRD_RPC_URL", "https://songbird-api.flare.network/ext/C/rpc")

# GraphQL configuration
FLARE_GRAPHQL_URL: str = os.getenv("FLARE_GRAPHQL_URL", "https://flare-explorer.flare.network/graphql")

# WebDriver configuration
CHROMIUM_BINARY: Optional[str] = os.getenv("CHROMIUM_BINARY")
CHROMEDRIVER: Optional[str] = os.getenv("CHROMEDRIVER")

# Snapshot configuration
SNAPSHOT_RETRIES: int = int(os.getenv("SNAPSHOT_RETRIES", "6"))
SNAPSHOT_RETRY_DELAY: int = int(os.getenv("SNAPSHOT_RETRY_DELAY", "600"))

# Validate critical configuration
def validate_config() -> None:
    """Validate that required configuration values are present."""
    errors = []
    
    if EMAIL_USER and not EMAIL_PASS:
        errors.append("EMAIL_PASS required when EMAIL_USER is set")
    
    if EMAIL_PASS and not EMAIL_USER:
        errors.append("EMAIL_USER required when EMAIL_PASS is set")
        
    if errors:
        raise ValueError("Configuration errors: " + "; ".join(errors))
