import os

GEMINI_API_KEY = "შენი_GEMINI_API_KEY_აქ"

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None

LANGUAGES = {
    "KA": "ka", "EN": "en", "DE": "de", "FR": "fr", "ES": "es",
    "IT": "it", "RU": "ru", "TR": "tr", "ZH": "zh-CN", "JA": "ja",
    "AR": "ar", "UK": "uk", "PL": "pl", "EL": "el", "HE": "he"
}
LANG_NAMES = list(LANGUAGES.keys())
