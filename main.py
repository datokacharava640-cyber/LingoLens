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

# Android TTS (Text To Speech) support
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Locale = autoclass('java.util.Locale')
    ANDROID_TTS_AVAILABLE = True
except Exception:
    ANDROID_TTS_AVAILABLE = False

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None
SERVER_ENDPOINT = "https://lingo-lens-chi.vercel.app/api/translate"

TRANSLATIONS = {
    "ka": {"name": "ქართული", "title": "✨ LingoLens AI", "hint": "ჰკითხეთ LingoLens-ს...", "ready": "საიდან დავიწყოთ?"},
    "en": {"name": "English", "title": "✨ LingoLens AI", "hint": "Ask LingoLens...", "ready": "Where should we start?"},
    "es": {"name": "Español", "title": "✨ LingoLens AI", "hint": "Pregunta a LingoLens...", "ready": "¿Por dónde empezamos?"},
    "fr": {"name": "Français", "title": "✨ LingoLens AI", "hint": "Demandez à LingoLens...", "ready": "Par où commencer ?"},
    "de": {"name": "Deutsch", "title": "✨ LingoLens AI", "hint": "Fragen Sie LingoLens...", "ready": "Wo sollen wir anfangen?"},
    "ru": {"name": "Русский", "title": "✨ LingoLens AI", "hint": "Спросите LingoLens...", "ready": "С чего начнем?"}
}

# Loko maizina sy mendrika (Gemini style)
Window.clearcolor = (0.07, 0.09, 0.12, 1)
Window.softinput_mode = "below_target"

class LingoLensApp(App):
    def build(self):
        try:
            self.lang_keys = list(TRANSLATIONS.keys())
            self.lang_idx = 0
            self.t = TRANSLATIONS[self.lang_keys[self.lang_idx]]
            self.chat_history = []
            self.tts = None

            if ANDROID_TTS_AVAILABLE:
                try:
                    activity = PythonActivity.mActivity
                    self.tts = TextToSpeech(activity, None)
                except Exception as e:
                    print("TTS Init Error:", e)

            font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}

            root = BoxLayout(orientation='vertical', padding=16, spacing=12)

            # Header / Title Bar
            top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.08))
            self.title_label = Label(
                text=str(self.t["title"]), font_size=20, bold=True, 
                halign="left", color=(0.9, 0.95, 1, 1), **font_kwargs
            )
            self.title_label.bind(size=lambda s, w: setattr(s, 'text_size', (w, None)))
            top_layout.add_widget(self.title_label)

            self.lang_btn = Button(
                text=f"🌐 {self.t['name']}", size_hint=(None, 1), width=110,
                background_color=(0.15, 0.2, 0.3, 1), color=(1, 1, 1, 1),
                on_press=self.switch_language, **font_kwargs
            )
            top_layout.add_widget(self.lang_btn)
            root.add_widget(top_layout)

            # Chat Scroll View Area
            scroll = ScrollView(size_hint=(1, 0.68), bar_width=4)
            self.output_label = Label(
                text=str(self.t["ready"]), font_size=16, halign="left", valign="top", 
                size_hint_y=None, color=(0.85, 0.9, 0.95, 1), **font_kwargs
            )
            self.output_label.bind(
                width=lambda s, w: setattr(s, 'text_size', (w - 15, None)),
                texture_size=lambda s, t: setattr(s, 'height', max(t[1], 150))
            )
            scroll.add_widget(self.output_label)
            root.add_widget(scroll)

            # Input Box & Controls Layout (Gemini Style Bar)
            input_container = BoxLayout(orientation='vertical', spacing=8, size_hint=(1, 0.18))
            
            self.text_input = TextInput(
                hint_text=self.t["hint"], multiline=False, size_hint=(1, 0.55),
                padding=[12, 12, 12, 12], background_color=(0.13, 0.17, 0.24, 1),
                foreground_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.55, 0.65, 1), **font_kwargs
            )
            input_container.add_widget(self.text_input)

            bottom_actions = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.45))
            
            self.send_btn = Button(
                text="გაგზავნა 🚀", size_hint=(0.6, 1),
                background_color=(0.2, 0.5, 0.9, 1), color=(1, 1, 1, 1),
                on_press=self.send_message, **font_kwargs
            )
            bottom_actions.add_widget(self.send_btn)

            self.speak_btn = Button(text="🔊 ხმა", size_hint=(0.4, 1),
                background_color=(0.15, 0.2, 0.3, 1), color=(1, 1, 1, 1),
                on_press=self.speak_response, **font_kwargs
            )
            bottom_actions.add_widget(self.speak_btn)

            input_container.add_widget(bottom_actions)
            root.add_widget(input_container)

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
        self.text_input.hint_text = self.t["hint"]
        if not self.chat_history:
            self.update_ui(self.t["ready"])

    def send_message(self, instance):
        msg = self.text_input.text.strip()
        if not msg:
            return

        self.text_input.text = ""
        target_lang = self.t["name"]
        self.chat_history.append(f"User: {msg}")
        self.update_ui("⏳ ფიქრობს...")

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
    LingoLensApp().run()
