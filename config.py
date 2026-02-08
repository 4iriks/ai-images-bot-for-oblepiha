from dataclasses import dataclass, field
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    bot_token: str = field(default_factory=lambda: getenv("BOT_TOKEN", ""))
    gemini_api_key: str = field(default_factory=lambda: getenv("GEMINI_API_KEY", ""))
    pollinations_api_keys: list[str] = field(default_factory=lambda: [
        k.strip() for k in getenv("POLLINATIONS_API_KEYS", "").split(",") if k.strip()
    ])
    required_channel: str = field(default_factory=lambda: getenv("REQUIRED_CHANNEL", ""))
    required_bot: str = field(default_factory=lambda: getenv("REQUIRED_BOT", ""))
    log_chat_id: int = field(default_factory=lambda: int(getenv("LOG_CHAT_ID", "0")))
    admin_id: int = field(default_factory=lambda: int(getenv("ADMIN_ID", "0")))

    def __post_init__(self):
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is required")


settings = Settings()
