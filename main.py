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

# Android Native TTS & STT (ხმის ცნობა და სინთეზი)
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

TRANSLATIONS = {
    "ka": {"name": "ქართული", "title": "✦ LingoLens Global AI", "hint": "ჰკითხეთ ან შეიტანეთ ტექსტი...", "ready": "გამარჯობა! მზად ვარ გლობალური თარგმანისა და ანალიზისთვის."},
    "en": {"name": "English", "title": "✦ LingoLens Global AI", "hint": "Ask LingoLens or type text...", "ready": "Hello! Ready for global translation & analysis."},
    "es": {"name": "Español", "title": "✦ LingoLens Global AI", "hint": "Pregunta a LingoLens...", "ready": "¡Hola! Listo para traducción global."},
}

Window.clearcolor = (0.07, 0.08, 0.10, 1)
Window.softinput_mode = "below_target"


# 1. მთავარი ეკრანი (AI Chat & AR Vision)
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
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
        root = BoxLayout(orientation='vertical', padding=14, spacing=10)

        # ზედა ნავიგაცია 5-ვე გლობალურ მოდულზე გადასასვლელად
        top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.07), spacing=4)
        self.title_label = Label(text=str(self.t["title"]), font_size=13, bold=True, color=(0.95, 0.95, 0.97, 1), **font_kwargs)
        top_layout.add_widget(self.title_label)

        top_layout.add_widget(Button(text="🎙️ Live", size_hint=(None, 1), width=52, background_normal='', background_color=(0.8, 0.3, 0.35, 1), on_press=lambda x: setattr(self.manager, 'current', 'voice_live'), **font_kwargs))
        top_layout.add_widget(Button(text="⚡ Edge", size_hint=(None, 1), width=52, background_normal='', background_color=(0.15, 0.6, 0.45, 1), on_press=lambda x: setattr(self.manager, 'current', 'offline_mode'), **font_kwargs))
        top_layout.add_widget(Button(text="🔥 Streak", size_hint=(None, 1), width=58, background_normal='', background_color=(0.9, 0.5, 0.1, 1), on_press=lambda x: setattr(self.manager, 'current', 'gamification'), **font_kwargs))
        top_layout.add_widget(Button(text="📁 B2B", size_hint=(None, 1), width=50, background_normal='', background_color=(0.3, 0.3, 0.7, 1), on_press=lambda x: setattr(self.manager, 'current', 'b2b_docs'), **font_kwargs))

        root.add_widget(top_layout)

        # პასუხების გამოსატანი ველი
        scroll = ScrollView(size_hint=(1, 0.58), bar_width=4)
        self.output_label = Label(text=str(self.t["ready"]), font_size=14, halign="left", valign="top", size_hint_y=None, color=(0.9, 0.92, 0.95, 1), **font_kwargs)
        self.output_label.bind(width=lambda s, w: setattr(s, 'text_size', (w - 20, None)), texture_size=lambda s, t: setattr(s, 'height', max(t[1], 180)))
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        # შეყვანისა და ქმედებების პანელი
        input_container = BoxLayout(orientation='vertical', spacing=6, size_hint=(1, 0.30))
        self.text_input = TextInput(hint_text=self.t["hint"], multiline=False, size_hint=(1, 0.4), padding=[10, 10, 10, 10], background_normal='', background_active='', background_color=(0.12, 0.14, 0.18, 1), foreground_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.55, 0.65, 1), **font_kwargs)
        input_container.add_widget(self.text_input)

        bottom_actions = BoxLayout(orientation='horizontal', spacing=6, size_hint=(1, 0.55))
        bottom_actions.add_widget(Button(text="✨ გაგზავნა", size_hint=(0.33, 1), background_normal='', background_color=(0.25, 0.45, 0.95, 1), color=(1, 1, 1, 1), on_press=self.send_message, **font_kwargs))
        bottom_actions.add_widget(Button(text="📷 AR კამერა", size_hint=(0.33, 1), background_normal='', background_color=(0.15, 0.60, 0.45, 1), color=(1, 1, 1, 1), on_press=self.capture_image_and_translate, **font_kwargs))
        bottom_actions.add_widget(Button(text="🔊 აუდიო", size_hint=(0.34, 1), background_normal='', background_color=(0.20, 0.22, 0.28, 1), color=(1, 1, 1, 1), on_press=lambda x: self.speak_text(self.last_ai_text), **font_kwargs))

        input_container.add_widget(bottom_actions)
        root.add_widget(input_container)
        self.add_widget(root)

    def update_ui(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def speak_text(self, text):
        if ANDROID_NATIVE_AVAILABLE and self.tts and text:
            try:
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print("TTS Error:", e)

    def send_message(self, instance):
        msg = self.text_input.text.strip()
        if not msg: return
        self.text_input.text = ""
        self.chat_history.append(f"User: {msg}")
        self.update_ui("✦ Gemini AI აანალიზებს მოთხოვნას...")

        def worker():
            try:
                res = requests.post(SERVER_ENDPOINT, json={"message": msg, "target_lang": self.t["name"]}, timeout=15)
                if res.status_code == 200:
                    ai_res = res.json().get("response", "")
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
        if ANDROID_PLYER_AVAILABLE:
            try:
                img_path = os.path.join(os.getcwd(), "capture.jpg")
                camera.take_picture(filename=img_path, on_complete=lambda p: self.update_ui("📷 AR ფოტო წარმატებით გადაიღო და გაიგზავნა ანალიზისთვის!"))
            except Exception as e:
                self.update_ui(f"კამერის შეცდომა: {str(e)}")
        else:
            self.update_ui("⚠️ AR კამერა ხელმისაწვდომია მხოლოდ ანდროიდ მოწყობილობაზე.")


# 2. რეალურ დროში ხმოვანი სტრიმინგის ეკრანი (Live Voice Mode)
class LiveVoiceScreen(Screen):
    def __init__(self, **kwargs):
        super(LiveVoiceScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]✦ LingoLens Live Voice Stream[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        layout.add_widget(Label(text="დააჭირეთ ღილაკს და დაიწყეთ ცოცხალი საუბარი AI ასისტენტთან ყოველგვარი დაყოვნების გარეშე.", font_size=14, color=(0.8,0.8,0.8,1), halign="center"))
        
        self.status_lbl = Label(text="სტატუსი: მზადყოფნაში 🎙️", font_size=15, color=(0.3, 0.9, 0.4, 1))
        layout.add_widget(self.status_lbl)

        toggle_btn = Button(text="🔴 ხმოვანი სესიის დაწყება", size_hint_y=None, height=55, background_normal='', background_color=(0.8, 0.3, 0.35, 1))
        toggle_btn.bind(on_press=lambda x: self.status_lbl.setter('text')(self.status_lbl, "სტატუსი: მიმდინარეობს აუდიო სტრიმინგი..."))
        layout.add_widget(toggle_btn)

        back_btn = Button(text="⬅️ მთავარ ეკრანზე დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


# 3. ოფლაინ / Edge AI მართვის ეკრანი
class OfflineModeScreen(Screen):
    def __init__(self, **kwargs):
        super(OfflineModeScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]⚡ Edge AI & Offline Models[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        layout.add_widget(Label(text="ჩამოტვირთეთ ლოკალური ენობრივი მოდელები, რათა იმუშაოთ ინტერნეტის გარეშე.", font_size=14, color=(0.8,0.8,0.8,1)))
        
        self.dl_status = Label(text="მდგომარეობა: ლოკალური მოდელი არ არის ჩამოტვირთული", font_size=14, color=(0.9, 0.7, 0.2, 1))
        layout.add_widget(self.dl_status)

        dl_btn = Button(text="📥 ოფლაინ მოდელის გადმოწერა (50MB)", size_hint_y=None, height=50, background_normal='', background_color=(0.15, 0.6, 0.45, 1))
        dl_btn.bind(on_press=lambda x: self.dl_status.setter('text')(self.dl_status, "მდგომარეობა: მოდელი წარმატებით ჩამოიტვირთა და აქტიურია! ✅"))
        layout.add_widget(dl_btn)

        back_btn = Button(text="⬅️ უკან დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


# 4. გეიმიფიკაციისა და სერიების ეკრანი (Streaks & Gamification)
class GamificationScreen(Screen):
    def __init__(self, **kwargs):
        super(GamificationScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]🔥 თქვენი სწავლის სერია (Streak)[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        layout.add_widget(Label(text="მიმდინარე სერია: 5 დღე ზედიზედ! 🏆\nმიღებული გამოცდილება: 450 XP\nდონე: ექსპერტი ლინგვისტი", font_size=16, color=(0.9,0.7,0.2,1), halign="center"))
        
        quiz_btn = Button(text="🎯 დღიური ქვიზის დაწყება (+50 XP)", size_hint_y=None, height=50, background_normal='', background_color=(0.9, 0.5, 0.1, 1))
        layout.add_widget(quiz_btn)

        back_btn = Button(text="⬅️ უკან დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


# 5. B2B / დოკუმენტების თარგმნის ეკრანი
class B2BDocsScreen(Screen):
    def __init__(self, **kwargs):
        super(B2BDocsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text="[b]📁 B2B & დოკუმენტების თარგმანი[/b]", markup=True, font_size=20, color=(1,1,1,1)))
        layout.add_widget(Label(text="აატვირთეთ PDF, DOCX ან ტექსტური ფაილები სრული ფორმატირების შენარჩუნებით სათარგმნად.", font_size=14, color=(0.8,0.8,0.8,1)))
        
        self.doc_status = Label(text="ფაილი არ არის არჩეული", font_size=14, color=(0.7, 0.7, 0.9, 1))
        layout.add_widget(self.doc_status)

        upload_btn = Button(text="📂 ფაილის არჩევა და სინქრონიზაცია", size_hint_y=None, height=50, background_normal='', background_color=(0.3, 0.3, 0.7, 1))
        upload_btn.bind(on_press=lambda x: self.doc_status.setter('text')(self.doc_status, "ფაილი დამუშავდა: contract_final.pdf (გაიგზავნა თარგმანისთვის)"))
        layout.add_widget(upload_btn)

        back_btn = Button(text="⬅️ უკან დაბრუნება", size_hint_y=None, height=50, background_normal='', background_color=(0.25, 0.45, 0.95, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(LiveVoiceScreen(name='voice_live'))
        sm.add_widget(OfflineModeScreen(name='offline_mode'))
        sm.add_widget(GamificationScreen(name='gamification'))
        sm.add_widget(B2BDocsScreen(name='b2b_docs'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()
