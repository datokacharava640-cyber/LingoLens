# modules/live_interpreter.py
from kivy.utils import platform

class LiveInterpreterEngine:
    def __init__(self):
        self.live_mode = False
        self.tts = None
        self._init_tts()

    def _init_tts(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                activity = PythonActivity.mActivity
                
                # Android Native TextToSpeech ინიციალიზაცია
                self.tts = TextToSpeech(activity, None)
                self.tts.setLanguage(Locale.US)
            except Exception as e:
                print(f"TTS Init Error: {e}")

    def speak_text(self, text):
        """ნათარგმნი ტექსტის ხმამაღლა წაკითხვა Android-ზე"""
        if platform == 'android' and self.tts:
            try:
                from jnius import autoclass
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print(f"Speak Error: {e}")
        return f"🔊 Speaking: '{text}'"

    def toggle_handsfree_live(self):
        self.live_mode = not self.live_mode
        status = "ACTIVE (Listening both sides)" if self.live_mode else "PAUSED"
        return f"Hands-Free Live Conversation: {status}"

    def process_live_speech(self, input_audio_text, detected_emotion="Neutral"):
        if not input_audio_text:
            return "Live Mode: Waiting for speech..."
        translated = f"Live Translation ({detected_emotion}): {input_audio_text}"
        self.speak_text(translated)
        return translated

    def ar_live_overlay(self, image_frame=None):
        return "Real-Time AR: Overlaying translation on live camera view."
