# modules/smart_features.py
import json
import os

class SmartAppEngine:
    def __init__(self, storage_file="translation_history.json"):
        self.storage_file = storage_file
        self.history = self.load_history()

    def load_history(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_translation(self, original, translated):
        entry = {"original": original, "translated": translated}
        self.history.append(entry)
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self.history[-50:], f, ensure_ascii=False, indent=2) # ინახავს ბოლო 50 თარგმანს
        except Exception:
            pass
        return f"💾 Saved to local history ({len(self.history)} items)"

    def auto_detect_and_route(self, text):
        if not text:
            return "Auto-Detect: No input"
        # მარტივი ლოგიკა ქართული/ლათინური ასოების აპარატურული ამოცნობისთვის
        has_georgian = any('\u10a0' <= char <= '\u10ff' for char in text)
        target = "en" if has_georgian else "ka"
        return f"🌐 Auto-Detected Language | Routing to: {target.upper()}"
