from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
import threading
import requests
import os
import traceback

# Android TTS (Text To Speech) მხარდაჭერა
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Locale = autoclass('java.util.Locale')
    ANDROID_TTS_AVAILABLE = True
except Exception:
    ANDROID_TTS_AVAILABLE = False

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None
SERVER_ENDPOINT = "https://lingo-lens-oj4u.vercel.app/api/translate"

TRANSLATIONS = {
    "ka": {"name": "ქართული", "title": "LingoLens AI — Power Engine", "ready": "AI სერვერი და ხმა მზადაა..."},
    "en": {"name": "English", "title": "LingoLens AI — Live Dialogue", "ready": "System Online..."},
    "es": {"name": "Español", "title": "LingoLens AI — Voz & IA", "ready": "Sistema Listo..."},
    "fr": {"name": "Français", "title": "LingoLens AI — Intelligence Vocale", "ready": "Prêt..."},
    "de": {"name": "Deutsch", "title": "LingoLens AI — Sprach-KI", "ready": "Bereit..."},
    "ru": {"name": "Русский", "title": "LingoLens AI — ИИ Помощник", "ready": "Система готова..."}
}

Window.softinput_mode = "below_target"

class LingoLensGiantApp(App):
    def build(self):
        try:
            self.lang_keys = list(TRANSLATIONS.keys())
            self.lang_idx = 0
            self.t = TRANSLATIONS[self.lang_keys[self.lang_idx]]
            self.chat_history = []
            self.tts = None

            # Android-ის ხმოვანი ძრავის ინიციალიზაცია
            if ANDROID_TTS_AVAILABLE:
                try:
                    activity = PythonActivity.mActivity
                    self.tts = TextToSpeech(activity, None)
                except Exception as e:
                    print("TTS Init Error:", e)

            font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}

            root = BoxLayout(orientation='vertical', padding=12, spacing=8)

            # სათაური
            self.title_label = Label(text=str(self.t["title"]), font_size=18, bold=True, size_hint=(1, 0.08), **font_kwargs)
            root.add_widget(self.title_label)

            # ჩატის ეკრანი
            scroll = ScrollView(size_hint=(1, 0.55))
            self.output_label = Label(text=str(self.t["ready"]), font_size=15, halign="left", valign="top", size_hint_y=None, **font_kwargs)
            self.output_label.bind(
                width=lambda s, w: setattr(s, 'text_size', (w - 10, None)),
                texture_size=lambda s, t: setattr(s, 'height', max(t[1], 100))
            )
            scroll.add_widget(self.output_label)
            root.add_widget(scroll)

            # ტექსტის შესაყვანი
            input_box = BoxLayout(orientation='horizontal', spacing=6, size_hint=(1, 0.12))
            self.text_input = TextInput(hint_text="ჩაწერეთ ტექსტი...", multiline=False, size_hint=(0.7, 1), padding=[8, 8, 8, 8], **font_kwargs)
            input_box.add_widget(self.text_input)

            self.send_btn = Button(text="გაგზავნა 🚀", size_hint=(0.3, 1), on_press=self.send_message, **font_kwargs)
            input_box.add_widget(self.send_btn)
            root.add_widget(input_box)

            # ხმოვანი და ენის მართვის ღილაკები
            controls = BoxLayout(orientation='horizontal', spacing=6, size_hint=(1, 0.10))
            self.speak_btn = Button(text="🔊 ხმით წაკითხვა", on_press=self.speak_response, **font_kwargs)
            controls.add_widget(self.speak_btn)

            self.lang_btn = Button(text=f"🌐 {self.t['name']}", on_press=self.switch_language, **font_kwargs)
            controls.add_widget(self.lang_btn)
            root.add_widget(controls)

            self.last_ai_text = ""
            return root

        except Exception:
            err = traceback.format_exc()
            box = BoxLayout(orientation='vertical', padding=10)
            box.add_widget(Label(text=f"App Error:\n{err}", font_size=11))
            return box

    def update_ui(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def speak_text(self, text):
        if ANDROID_TTS_AVAILABLE and self.tts:
            try:
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print("TTS Speak Error:", e)

    def speak_response(self, instance):
        if self.last_ai_text:
            self.speak_text(self.last_ai_text)

    def switch_language(self, instance):
        self.lang_idx = (self.lang_idx + 1) % len(self.lang_keys)
        self.t = TRANSLATIONS[self.lang_keys[self.lang_idx]]
        self.title_label.text = str(self.t["title"])
        self.lang_btn.text = f"🌐 {self.t['name']}"

    def send_message(self, instance):
        msg = self.text_input.text.strip()
        if not msg:
            return

        self.text_input.text = ""
        target_lang = self.t["name"]
        self.chat_history.append(f"User: {msg}")
        self.update_ui("⏳ LingoLens სერვერთან და Gemini AI-სთან კავშირი...")

        def worker():
            try:
                payload = {
                    "message": msg,
                    "target_lang": target_lang,
                    "history": self.chat_history[-4:]
                }
                res = requests.post(SERVER_ENDPOINT, json=payload, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    ai_res = data.get("response", "")
                    self.last_ai_text = ai_res
                    self.chat_history.append(f"AI: {ai_res}")
                    
                    full_text = "\n\n".join(self.chat_history[-6:])
                    self.update_ui(full_text)
                    
                    self.speak_text(ai_res)
                else:
                    self.update_ui(f"სერვერის შეცდომა [{res.status_code}]: შეამოწმეთ backend-ის ჰოსტინგი.")
            except Exception as e:
                self.update_ui(f"ქსელის / სერვერის შეცდომა: {str(e)}")

        threading.Thread(target=worker, daemon=True).start()

if __name__ == '__main__':
    LingoLensGiantApp().run()
