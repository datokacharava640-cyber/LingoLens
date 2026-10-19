from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.clock import Clock
import threading
import requests
import os
import base64
import traceback

# Android Native TTS და Hardware მხარდაჭერა (pyjnius & plyer)
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    ANDROID_TTS_AVAILABLE = True
except Exception:
    ANDROID_TTS_AVAILABLE = False

try:
    from plyer import camera, storage, vibrator
    ANDROID_PLYER_AVAILABLE = True
except Exception:
    ANDROID_PLYER_AVAILABLE = False

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None
SERVER_ENDPOINT = "https://lingo-lens-chi.vercel.app/api/translate"

TRANSLATIONS = {
    "ka": {"name": "ქართული", "title": "✨ LingoLens AI & MicroScope", "hint": "ჩაწერეთ ტექსტი...", "ready": "საიდან დავიწყოთ?"},
    "en": {"name": "English", "title": "✨ LingoLens AI & MicroScope", "hint": "Ask LingoLens...", "ready": "Where should we start?"},
    "es": {"name": "Español", "title": "✨ LingoLens AI & MicroScope", "hint": "Pregunta a LingoLens...", "ready": "¿Por dónde empezamos?"},
    "fr": {"name": "Français", "title": "✨ LingoLens AI & MicroScope", "hint": "Demandez à LingoLens...", "ready": "Par où commencer ?"},
    "de": {"name": "Deutsch", "title": "✨ LingoLens AI & MicroScope", "hint": "Fragen Sie LingoLens...", "ready": "Wo sollen wir anfangen?"},
    "ru": {"name": "Русский", "title": "✨ LingoLens AI & MicroScope", "hint": "Спросите LingoLens...", "ready": "С чего начнем?"},
    "zh": {"name": "中文", "title": "✨ LingoLens AI & MicroScope", "hint": "询问 LingoLens...", "ready": "我们从哪里开始？"},
    "ja": {"name": "日本語", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens에 질문...", "ready": "どこから始めましょうか？"},
    "ar": {"name": "العربية", "title": "✨ LingoLens AI & MicroScope", "hint": "اسأل LingoLens...", "ready": "من أين نبدأ؟"},
    "hi": {"name": "हिन्दी", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens से पूछें...", "ready": "हम कहाँ से शुरू करें?"},
    "pt": {"name": "Português", "title": "✨ LingoLens AI & MicroScope", "hint": "Pergunte ao LingoLens...", "ready": "Por onde começamos?"},
    "it": {"name": "Italiano", "title": "✨ LingoLens AI & MicroScope", "hint": "Chiedi a LingoLens...", "ready": "Da dove iniziamo?"},
    "ko": {"name": "한국어", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens에게 질문하세요...", "ready": "어디부터 시작할까요?"},
    "tr": {"name": "Türkçe", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens'e sorun...", "ready": "Nereden başlayalım?"}
}

Window.clearcolor = (0.07, 0.09, 0.12, 1)
Window.softinput_mode = "below_target"


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        try:
            self.lang_keys = list(TRANSLATIONS.keys())
            self.lang_idx = 0
            self.t = TRANSLATIONS[self.lang_keys[self.lang_idx]]
            self.chat_history = []
            self.tts = None
            self.last_ai_text = ""

            if ANDROID_TTS_AVAILABLE:
                try:
                    activity = PythonActivity.mActivity
                    self.tts = TextToSpeech(activity, None)
                except Exception as e:
                    print("TTS Init Error:", e)

            font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}

            root = BoxLayout(orientation='vertical', padding=14, spacing=10)

            top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), spacing=6)
            self.title_label = Label(
                text=str(self.t["title"]), font_size=15, bold=True, 
                halign="left", color=(0.9, 0.95, 1, 1), **font_kwargs
            )
            self.title_label.bind(size=lambda s, w: setattr(s, 'text_size', (w, None)))
            top_layout.add_widget(self.title_label)

            self.voice_nav_btn = Button(
                text="✈️ ხმა", size_hint=(None, 1), width=75,
                background_color=(0.2, 0.7, 0.4, 1), color=(1, 1, 1, 1),
                on_press=lambda x: setattr(self.manager, 'current', 'voice_translator'), **font_kwargs
            )
            top_layout.add_widget(self.voice_nav_btn)

            self.lang_btn = Button(
                text=f"🌐 {self.t['name']}", size_hint=(None, 1), width=90,
                background_color=(0.15, 0.2, 0.3, 1), color=(1, 1, 1, 1),
                on_press=self.switch_language, **font_kwargs
            )
            top_layout.add_widget(self.lang_btn)
            root.add_widget(top_layout)

            scroll = ScrollView(size_hint=(1, 0.62), bar_width=4)
            self.output_label = Label(
                text=str(self.t["ready"]), font_size=15, halign="left", valign="top", 
                size_hint_y=None, color=(0.85, 0.9, 0.95, 1), **font_kwargs
            )
            self.output_label.bind(
                width=lambda s, w: setattr(s, 'text_size', (w - 15, None)),
                texture_size=lambda s, t: setattr(s, 'height', max(t[1], 150))
            )
            scroll.add_widget(self.output_label)
            root.add_widget(scroll)

            input_container = BoxLayout(orientation='vertical', spacing=6, size_hint=(1, 0.24))
            
            self.text_input = TextInput(
                hint_text=self.t["hint"], multiline=False, size_hint=(1, 0.45),
                padding=[10, 10, 10, 10], background_color=(0.13, 0.17, 0.24, 1),
                foreground_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.55, 0.65, 1), **font_kwargs
            )
            input_container.add_widget(self.text_input)

            bottom_actions = BoxLayout(orientation='horizontal', spacing=6, size_hint=(1, 0.55))
            
            self.send_btn = Button(
                text="🚀 გაგზავნა", size_hint=(0.35, 1),
                background_color=(0.2, 0.5, 0.9, 1), color=(1, 1, 1, 1),
                on_press=self.send_message, **font_kwargs
            )
            bottom_actions.add_widget(self.send_btn)

            self.microscope_btn = Button(
                text="🔬 მიკროსკოპი", size_hint=(0.35, 1),
                background_color=(0.1, 0.6, 0.4, 1), color=(1, 1, 1, 1),
                on_press=self.analyze_microscope_image, **font_kwargs
            )
            bottom_actions.add_widget(self.microscope_btn)

            self.speak_btn = Button(
                text="🔊 ხმა", size_hint=(0.3, 1),
                background_color=(0.15, 0.2, 0.3, 1), color=(1, 1, 1, 1),
                on_press=self.speak_response, **font_kwargs
            )
            bottom_actions.add_widget(self.speak_btn)

            input_container.add_widget(bottom_actions)
            root.add_widget(input_container)

            self.add_widget(root)

        except Exception:
            err = traceback.format_exc()
            box = BoxLayout(orientation='vertical', padding=10)
            box.add_widget(Label(text=f"App Error:\n{err}", font_size=11))
            self.add_widget(box)

    def update_ui(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def speak_text(self, text):
        if ANDROID_TTS_AVAILABLE and self.tts:
            try:
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print("TTS Error:", e)

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
        self.update_ui("⏳ Gemini AI ფიქრობს...")

        def worker():
            try:
                payload = {
                    "message": msg,
                    "target_lang": target_lang,
                    "history": self.chat_history[-4:]
                }
                res = requests.post(SERVER_ENDPOINT, json=payload, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    ai_res = data.get("response", "")
                    self.last_ai_text = ai_res
                    self.chat_history.append(f"AI: {ai_res}")
                    
                    full_text = "\n\n".join(self.chat_history[-6:])
                    self.update_ui(full_text)
                    self.speak_text(ai_res)
                else:
                    self.update_ui(f"სერვერის შეცდომა [{res.status_code}]")
            except Exception as e:
                self.update_ui(f"ქსელის შეცდომა: {str(e)}")

        threading.Thread(target=worker, daemon=True).start()

    def analyze_microscope_image(self, instance):
        img_path = "microscope_capture.jpg"
        if ANDROID_PLYER_AVAILABLE:
            try:
                pass
            except Exception:
                pass

        if not os.path.exists(img_path):
            img_path = "sample.jpg"

        if not os.path.exists(img_path):
            self.update_ui("⚠️ მიკროსკოპის ფოტო ვერ მოიძებნა (microscope_capture.jpg).")
            return

        self.update_ui("🔬 მიკროსკოპული გამოსახულების ანალიზი Gemini AI-ს მეშვეობით...")

        def image_worker():
            try:
                with open(img_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

                payload = {
                    "image_base64": encoded_string,
                    "message": "გააანალიზე ეს მიკროსკოპული გამოსახულება დეტალურად.",
                    "target_lang": self.t["name"]
                }
                res = requests.post(SERVER_ENDPOINT, json=payload, timeout=20)
                if res.status_code == 200:
                    data = res.json()
                    ai_res = data.get("response", "")
                    self.last_ai_text = ai_res
                    self.chat_history.append(f"🔬 AI MicroScope: {ai_res}")
                    
                    full_text = "\n\n".join(self.chat_history[-6:])
                    self.update_ui(full_text)
                    self.speak_text(ai_res)
                else:
                    self.update_ui(f"ანალიზის შეცდომა სერვერზე [{res.status_code}]")
            except Exception as e:
                self.update_ui(f"ფოტოს დამუშავების შეცდომა: {str(e)}")

        threading.Thread(target=image_worker, daemon=True).start()


class VoiceTranslatorScreen(Screen):
    def __init__(self, **kwargs):
        super(VoiceTranslatorScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title = Label(
            text="[b]LingoLens Voice Translator[/b]",
            markup=True,
            font_size='22sp',
            size_hint_y=None,
            height=50
        )
        layout.add_widget(title)
        
        lang_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
        self.src_spinner = Spinner(text='ka', values=('ka', 'en', 'ru', 'de', 'fr', 'es', 'tr'), size_hint_x=0.4)
        arrow_label = Label(text="➔", size_hint_x=0.2)
        self.target_spinner = Spinner(text='en', values=('en', 'ka', 'ru', 'de', 'fr', 'es', 'tr'), size_hint_x=0.4)
        
        lang_layout.add_widget(self.src_spinner)
        lang_layout.add_widget(arrow_label)
        lang_layout.add_widget(self.target_spinner)
        layout.add_widget(lang_layout)
        
        self.status_label = Label(
            text="ჩაწერეთ ტექსტი ან გამოიყენეთ თარგმანი სერვერით...",
            font_size='16sp',
            size_hint_y=None,
            height=40
        )
        layout.add_widget(self.status_label)
        
        self.result_label = Label(
            text="",
            font_size='18sp',
            color=(0.2, 0.8, 0.2, 1)
        )
        layout.add_widget(self.result_label)
        
        self.voice_input = TextInput(
            hint_text="ჩაწერეთ სათარგმნი ფრაზა...",
            multiline=False,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.voice_input)
        
        self.translate_btn = Button(
            text="🌐 თარგმნა და გაჟღერება",
            font_size='18sp',
            size_hint_y=None,
            height=60,
            background_color=(0.2, 0.6, 1, 1)
        )
        self.translate_btn.bind(on_press=self.translate_text_server)
        layout.add_widget(self.translate_btn)
        
        back_btn = Button(
            text="⬅️ მთავარ მენიუში დაბრუნება",
            size_hint_y=None,
            height=50,
            background_color=(0.3, 0.3, 0.3, 1)
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)

    def translate_text_server(self, instance):
        text = self.voice_input.text.strip()
        if not text:
            return
        
        src_lang = self.src_spinner.text
        target_lang = self.target_spinner.text
        self.status_label.text = "ითარგმნება..."

        def worker():
            try:
                payload = {
                    "message": f"Translate this from {src_lang} to {target_lang}: {text}",
                    "target_lang": target_lang
                }
                res = requests.post(SERVER_ENDPOINT, json=payload, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    translated = data.get("response", text)
                    Clock.schedule_once(lambda dt: self.update_result(text, translated, target_lang))
                else:
                    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f"შეცდომა: {res.status_code}"))
            except Exception as e:
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f"შეცდომა: {str(e)}"))

        threading.Thread(target=worker, daemon=True).start()

    def update_result(self, original, translated, lang):
        self.result_label.text = f"ორიგინალი: {original}\n\nთარგმანი: {translated}"
        self.status_label.text = "მზად არის!"
        if ANDROID_TTS_AVAILABLE:
            try:
                pass
            except Exception:
                pass


class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(VoiceTranslatorScreen(name='voice_translator'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()
