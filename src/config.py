import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    HERO_SMS_API_KEY: str = field(default_factory=lambda: os.getenv("HERO_SMS_API_KEY", ""))
    WEBHOOK_URL: str = field(default_factory=lambda: os.getenv("WEBHOOK_URL", "http://localhost"))
    WEBHOOK_SECRET_TOKEN: str = field(default_factory=lambda: os.getenv("WEBHOOK_SECRET_TOKEN", ""))
    DATABASE_URL: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data.db"))
    WEBHOOK_PATH: str = "/webhook"
    WEBAPP_HOST: str = "0.0.0.0"
    WEBAPP_PORT: int = 8080

    @property
    def webhook_full_url(self) -> str:
        return f"{self.WEBHOOK_URL.rstrip('/')}{self.WEBHOOK_PATH}"
