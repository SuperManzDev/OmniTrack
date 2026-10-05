import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_models: list = field(default_factory=lambda: [
        m.strip() for m in os.getenv("OPENROUTER_MODELS", "inclusionai/ling-3.0-flash-fin:free,liquid/lfm-2.5-2.6b:free,nvidia/nemotron-3.5-lightning:free").split(",") if m.strip()
    ])
    
    # Gmail & SMS Gateway
    gmail_sender: str = os.getenv("GMAIL_SENDER", "")
    gmail_app_password: str = os.getenv("GMAIL_APP_PASSWORD", "")
    gmail_recipient: str = os.getenv("GMAIL_RECIPIENT", "")
    sms_phone_number: str = os.getenv("SMS_PHONE_NUMBER", "")
    sms_carrier: str = os.getenv("SMS_CARRIER", "att")
    
    # Snapchat Backup
    snap_username: str = os.getenv("SNAP_USERNAME", "")
    snap_password: str = os.getenv("SNAP_PASSWORD", "")
    snap_group_name: str = os.getenv("SNAP_GROUP_NAME", "")
    snap_friend_username: str = os.getenv("SNAP_FRIEND_USERNAME", "")
    snap_auth_path: str = os.path.join(os.path.dirname(__file__), "snap_auth.json")
    
    check_interval_minutes: int = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))
    packages_file: str = os.path.join(os.path.dirname(__file__), "packages.json")
    storage_file: str = os.path.join(os.path.dirname(__file__), "packages.json")

config = Config()
