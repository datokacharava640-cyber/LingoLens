from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock
import threading
import requests
import os
import base64
import traceback

# Android Native TTS & STT (ხმის ცნობა) pyjnius და plyer-ის მეშვეობით
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Intent = autoclass('android.content.Intent')
    RecognizerIntent = autoclass('android.speech.RecognizerIntent')
    ANDROID_NATIVE_AVAILABLE = True
except Exception:
    ANDROID_NATIVE_AVAILABLE = False

try:
    from plyer import camera, vibrator
    ANDROID_PLYER_AVAILABLE = True
except Exception:
    ANDROID_PLYER_AVAILABLE = False

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None
SERVER_ENDPOINT = "https://lingo-lens-chi.vercel.app/api/translate"

# მსოფლიოს წამყვანი ენების ლექსიკონი LingoLens AI-სთვის
TRANSLATIONS = {
    "ka": {"name": "ქართული", "title": "✦ LingoLens Gemini AI", "hint": "ჰკითხეთ ან შეიტანეთ ტექსტი...", "ready": "გამარჯობა! რით შემიძლია დაგეხმაროთ დღეს?"},
    "en": {"name": "English", "title": "✦ LingoLens Gemini AI", "hint": "Ask LingoLens or type text...", "ready": "Hello! How can I help you today?"},
    "es": {"name": "Español", "title": "✦ LingoLens Gemini AI", "hint": "Pregunta a LingoLens...", "ready": "¡Hola! ¿Cómo puedo ayudarte hoy?"},
    "fr": {"name": "Français", "title": "✦ LingoLens Gemini AI", "hint": "Demandez à LingoLens...", "ready": "Bonjour ! Comment puis-je vous aider ?"},
    "de": {"name": "Deutsch", "title": "✦ LingoLens Gemini AI", "hint": "Fragen Sie LingoLens...", "ready": "Hallo! Wie kann ich Ihnen heute helfen?"},
    "ru": {"name": "Русский", "title": "✦ LingoLens Gemini AI", "hint": "Спросите LingoLens...", "ready": "Здравствуйте! Чем я могу помочь?"}
}

# Gemini-ს სტილის ფონური ფერი (მუქი, პრემიუმ ტონალობა)
Window.clearcolor = (0.07, 0.08, 0.10, 1)
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

            if ANDROID_NATIVE_AVAILABLE:
                try:
                    activity = PythonActivity.mActivity
                    self.tts = TextToSpeech(activity, None)
                except Exception as e:
                    print("TTS Init Error:", e)

            font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}

            # მთავარი კონტეინერი Gemini სტილის განლაგებით
            root = BoxLayout(orientation='vertical', padding=16, spacing=12)

            # ზედა პანელი (სათაური და ენის/ხმის ღილაკები)
            top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), spacing=8)
            self.title_label = Label(
                text=str(self.t["title"]), font_size=16, bold=True, 
                halign="left", color=(0.95, 0.95, 0.97, 1), **font_kwargs
            )
            top_layout.add_widget(self.title_label)

            self.voice_nav_btn = Button(
                text="🎙️ ხმა", size_hint=(None, 1), width=70,
                background_normal='', background_color=(0.18, 0.20, 0.25, 1), color=(0.9, 0.9, 1, 1),
                on_press=lambda x: setattr(self.manager, 'current', 'voice_translator'), **font_kwargs
            )
            top_layout.add_widget(self.voice_nav_btn)

            self.lang_btn = Button(
                text=f"🌐 {self.t['name']}", size_hint=(None, 1), width=100,
                background_normal='', background_color=(0.18, 0.20, 0.25, 1), color=(0.9, 0.9, 1, 1),
                on_press=self.switch_language, **font_kwargs
            )
            top_layout.add_widget(self.lang_btn)
            root.add_widget(top_layout)

            # პასუხების გამოსატანი ველი (Gemini სტილის ბარათი)
            scroll = ScrollView(size_hint=(1, 0.54), bar_width=4)
            self.output_label = Label(
                text=str(self.t["ready"]), font_size=15, halign="left", valign="top", 
                size_hint_y=None, color=(0.9, 0.92, 0.95, 1), **font_kwargs
            )
            self.output_label.bind(
                width=lambda s, w: setattr(s, 'text_size', (w - 20, None)),
                texture_size=lambda s, t: setattr(s, 'height', max(t[1], 180))
            )
            scroll.add_widget(self.output_label)
            root.add_widget(scroll)

            # შეყვანისა და ქმედებების პანელი
            input_container = BoxLayout(orientation='vertical', spacing=8, size_hint=(1, 0.32))
            
            self.text_input = TextInput(
                hint_text=self.t["hint"], multiline=False, size_hint=(1, 0.38),
                padding=[12, 12, 12, 12], background_normal='', background_active='',
                background_color=(0.12, 0.14, 0.18, 1),
                foreground_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.55, 0.65, 1), **font_kwargs
            )
            input_container.add_widget(self.text_input)

            # Gemini სტილის თანამედროვე მრგვალი/კონტურული ღილაკები
            bottom_actions = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.58))
            
            self.send_btn = Button(
                text="✨ გაგზავნა", size_hint=(0.25, 1),
                background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1),
                on_press=self.send_message, **font_kwargs
            )
            bottom_actions.add_widget(self.send_btn)

            # კამერით გადაღებისა და თარგმნის ღილაკი
            self.camera_btn = Button(
                text="📷 კამერა", size_hint=(0.25, 1),
                background_normal='', background_color=(0.15, 0.60, 0.45, 1), color=(1, 1, 1, 1),
                on_press=self.capture_image_and_translate, **font_kwargs
            )
            bottom_actions.add_widget(self.camera_btn)

            self.stt_btn = Button(
                text="🎙️ საუბარი", size_hint=(0.25, 1),
                background_normal='', background_color=(0.80, 0.30, 0.35, 1), color=(1, 1, 1, 1),
                on_press=self.start_voice_agent, **font_kwargs
            )
            bottom_actions.add_widget(self.stt_btn)

            self.speak_btn = Button(
                text="🔊 აუდიო", size_hint=(0.25, 1),
                background_normal='', background_color=(0.20, 0.22, 0.28, 1), color=(1, 1, 1, 1),
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
        if ANDROID_NATIVE_AVAILABLE and self.tts:
            try:
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print("TTS Error:", e)

    def start_voice_agent(self, instance):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "გთხოვთ, ისაუბრეთ...")
                activity = PythonActivity.mActivity
                activity.startActivityForResult(intent, 100)
            except Exception as e:
                self.update_ui(f"ხმის ცნობის შეცდომა: {str(e)}")
        else:
            self.update_ui("⚠️ ხმოვანი აგენტი მუშაობს მხოლოდ ანდროიდ მოწყობილობაზე.")

    def speak_response(self, instance):
        if self.last_ai_text:
            self.speak_text(self.last_ai_text)

    def switch_language(self, instance):
        self.lang_idx = (self.lang_idx + 1) % len(self.lang_keys)
        self.t = TRANSLATIONS[self.lang_keys[self.lang_idx]]
        self.title_label.text = str(self.t["title"])
        self.lang_btn.text = f"🌐 {self.t['name']}"
        self.text_input.hint_text = self.t["hint"]

    def send_message(self, instance):
        msg = self.text_input.text.strip()
        if not msg:
            return

        self.text_input.text = ""
        target_lang = self.t["name"]
        self.chat_history.append(f"User: {msg}")
        self.update_ui("✦ Gemini AI ფიქრობს...")

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
                    self.update_ui("\n\n".join(self.chat_history[-6:]))
                    self.speak_text(ai_res)
                else:
                    self.update_ui(f"სერვერის შეცდომა [{res.status_code}]")
            except Exception as e:
                self.update_ui(f"ქსელის შეცდომა: {str(e)}")

        threading.Thread(target=worker, daemon=True).start()

    def capture_image_and_translate(self, instance):
        """კამერის გააქტიურება და ფოტოს გადაღება plyer-ის მეშვეობით"""
        if ANDROID_PLYER_AVAILABLE:
            try:
                img_path = os.path.join(os.getcwd(), "microscope_capture.jpg")
                camera.take_picture(filename=img_path, on_complete=self.camera_callback)
            except Exception as e:
                self.update_ui(f"კამერის შეცდომა: {str(e)}")
        else:
            self.update_ui("⚠️ კამერა ხელმისაწვდომია მხოლოდ ანდროიდ მოწყობილობაზე. ვამოწმებ არსებულ ფოტოს...")
            self.analyze_microscope_image(None)

    def camera_callback(self, filepath):
        """ფოტოს გადაღების დასრულების შემდეგ ავტომატურად იგზავნება ანალიზისთვის"""
        self.update_ui("📷 ფოტო წარმატებით გადაიღო! მიმდინარეობს Gemini AI ანალიზი...")
        self.analyze_microscope_image(None)

    def analyze_microscope_image(self, instance):
        img_path = "microscope_capture.jpg"
        if not os.path.exists(img_path):
            img_path = "sample.jpg"

        if not os.path.exists(img_path):
            self.update_ui("⚠️ ფოტო ვერ მოიძებნა. გთხოვთ, ჯერ გადაიღოთ ფოტო კამერით.")
            return

        self.update_ui("✦ Gemini AI აანალიზებს გადაღებულ გამოსახულებას...")

        def image_worker():
            try:
                with open(img_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

                payload = {
                    "image_base64": encoded_string,
                    "message": "გააანალიზე ეს გადაღებული ფოტო/ობიექტი დეტალურად და თარგმნე.",
                    "target_lang": self.t["name"]
                }
                res = requests.post(SERVER_ENDPOINT, json=payload, timeout=20)
                if res.status_code == 200:
                    data = res.json()
                    ai_res = data.get("response", "")
                    self.last_ai_text = ai_res
                    self.chat_history.append(f"✦ AI Vision: {ai_res}")
                    self.update_ui("\n\n".join(self.chat_history[-6:]))
                    self.speak_text(ai_res)
                else:
                    self.update_ui(f"სერვერის შეცდომა [{res.status_code}]")
            except Exception as e:
                self.update_ui(f"ფოტოს დამუშავების შეცდომა: {str(e)}")

        threading.Thread(target=image_worker, daemon=True).start()


class VoiceTranslatorScreen(Screen):
    def __init__(self, **kwargs):
        super(VoiceTranslatorScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        title = Label(text="[b]LingoLens Voice Mode[/b]", markup=True, font_size='22sp', size_hint_y=None, height=50, color=(1,1,1,1))
        layout.add_widget(title)

        back_btn = Button(
            text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, 
            background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1,1,1,1)
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(VoiceTranslatorScreen(name='voice_translator'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()
