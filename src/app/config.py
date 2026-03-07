from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseModel):
    app_name: str = "GreenBuild AI"
    gemini_api_key: str = ""
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    storage_file: Path = ROOT_DIR / "backend" / "storage" / "db.json"
    report_dir: Path = ROOT_DIR / "backend" / "storage" / "reports"
    gemini_model: str = "gemini-1.5-pro"


@lru_cache
def get_settings() -> Settings:
    import os

    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
    )

