import os

class Config:
    # GitHub Secrets-იდან ან სისტემიდან იღებს GEMINI_API_KEY-ს
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_FALLBACK_LOCAL_KEY_HERE")
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    DB_NAME = "lingolens.db"
    DEFAULT_FONT = "NotoSansGeorgian-Regular.ttf"
