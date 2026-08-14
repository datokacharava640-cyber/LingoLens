def handle_walkie_talkie(text, lang="en"):
    if not text:
        return "🎙️ Ready for Walkie-Talkie voice dialogue..."
    return f"🗣️ [Walkie-Talkie] ({lang}): {text}"
