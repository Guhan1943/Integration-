import os
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
    ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID", "1000.KGS01VMDWOZDWIAACTAIM3I05T8YIT")
    ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "e043da1c18b29c92cd3c74f10d3c089fd9bf1ef9bd")
    ZOHO_REDIRECT_URI = os.getenv(
        "ZOHO_REDIRECT_URI",
        "http://127.0.0.1:8000/api/hrms/callback/",
    )
    BAMBOO_API_KEY = os.getenv("BAMBOO_API_KEY") or os.getenv("BAMBOOHR_API_KEY", "")
    BAMBOO_SUBDOMAIN = os.getenv("BAMBOO_SUBDOMAIN") or os.getenv("BAMBOOHR_SUBDOMAIN", "")


settings = Settings()
