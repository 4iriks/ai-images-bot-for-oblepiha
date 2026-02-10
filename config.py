from dataclasses import dataclass, field
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    bot_token: str = field(default_factory=lambda: getenv("BOT_TOKEN", ""))
    api_url: str = field(default_factory=lambda: getenv("API_URL", "http://localhost:3000"))
    api_token: str = field(default_factory=lambda: getenv("API_TOKEN", ""))
    required_channel: str = field(default_factory=lambda: getenv("REQUIRED_CHANNEL", ""))
    required_bot: str = field(default_factory=lambda: getenv("REQUIRED_BOT", ""))
    bot_check_url: str = field(default_factory=lambda: getenv("BOT_CHECK_URL", ""))
    bot_check_api_key: str = field(default_factory=lambda: getenv("BOT_CHECK_API_KEY", ""))
    log_chat_id: int = field(default_factory=lambda: int(getenv("LOG_CHAT_ID") or "0"))
    admin_id: int = field(default_factory=lambda: int(getenv("ADMIN_ID") or "0"))
    db_path: str = field(default_factory=lambda: getenv("DB_PATH", "bot.db"))

    def __post_init__(self):
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is required")
        if not self.api_token:
            raise ValueError("API_TOKEN is required")


settings = Settings()
