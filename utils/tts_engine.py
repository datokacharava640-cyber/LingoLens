def speak(text, lang="en", user_dir="", callback=None):
    """ტექსტის ხმოვანი გამოთქმა plyer-ის ან Android TTS-ის გამოყენებით"""
    try:
        from plyer import tts
        tts.speak(text)
        if callback:
            callback("წარმატებით ითქვა")
    except Exception as e:
        if callback:
            callback(f"TTS შეცდომა: {str(e)}")
