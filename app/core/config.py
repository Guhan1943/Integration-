import os


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
    ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID", "1000.KGS01VMDWOZDWIAACTAIM3I05T8YIT")
    ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "e043da1c18b29c92cd3c74f10d3c089fd9bf1ef9bd")
    ZOHO_REDIRECT_URI = os.getenv(
        "ZOHO_REDIRECT_URI",
        "http://127.0.0.1:8000/api/hrms/callback/",
    )


settings = Settings()
