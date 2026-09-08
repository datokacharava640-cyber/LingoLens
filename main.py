import os
import sys
import json
import ssl
import threading
import time
import urllib.request
import urllib.parse

from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.graphics import Color, Rectangle
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup

# ლოკალური AI ძრავის იმპორტი
from offline_engine import OfflineTranslatorEngine

try:
    from config import GEMINI_API_KEY
except ImportError:
    GEMINI_API_KEY = ""

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None

LANGUAGES = {
    "ავტოდაჭერა": "auto",
    "ქართული": "ka",
    "ინგლისური": "en",
    "რუსული": "ru",
    "გერმანული": "de",
    "ფრანგული": "fr",
    "ესპანური": "es",
    "თურქული": "tr"
}

# ---------------------------------------------------------
# კროსპლატფორმული ვიბრაცია და ნებართვები
# ---------------------------------------------------------
def request_system_permissions():
    if platform == "android":
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.RECORD_AUDIO,
                Permission.CAMERA,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.VIBRATION
            ])
        except Exception as e:
            print(f"Android Permissions error: {e}")

def trigger_haptic_feedback():
    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            activity = PythonActivity.mActivity
            vibrator = activity.getSystemService(Context.VIBRATION_SERVICE)
            if vibrator and vibrator.hasVibrator():
                vibrator.vibrate(40)
        except Exception:
            pass

# ---------------------------------------------------------
# GUI პოპაპი
# ---------------------------------------------------------
class BasePopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if FONT_PATH:
            self.title_font = FONT_PATH
        self.background_color = (0.12, 0.08, 0.20, 0.95)
        self.title_color = (0.9, 0.8, 1, 1)

# ---------------------------------------------------------
# მთავარი ეკრანი
# ---------------------------------------------------------
class LingoLensMainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "auto"
        self.target_lang = "ka"
        self.offline_engine = OfflineTranslatorEngine()
        
        # Real-time Voice კონტროლი
        self.is_realtime_listening = False
        self.realtime_thread = None
        self.chat_container = None
        
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation="vertical", padding=12, spacing=8)

        with layout.canvas.before:
            Color(0.06, 0.03, 0.10, 1)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._update_bg, pos=self._update_bg)

        # 1. ენების პანელი
        lang_bar = BoxLayout(size_hint_y=None, height="45dp", spacing=6)
        
        btn_style = {"background_normal": "", "background_color": (0.22, 0.12, 0.35, 1), "color": (1, 1, 1, 1)}
        
        self.btn_src = Button(text="ავტოდაჭერა", size_hint_x=0.4, **btn_style)
        if FONT_PATH: self.btn_src.font_name = FONT_PATH
        self.btn_src.bind(on_release=lambda x: self.select_lang("source"))

        self.btn_swap = Button(text="⇄", size_hint_x=0.2, bold=True, **btn_style)
        self.btn_swap.bind(on_release=lambda x: self.swap_langs())

        self.btn_tgt = Button(text="ქართული", size_hint_x=0.4, **btn_style)
        if FONT_PATH: self.btn_tgt.font_name = FONT_PATH
        self.btn_tgt.bind(on_release=lambda x: self.select_lang("target"))

        lang_bar.add_widget(self.btn_src)
        lang_bar.add_widget(self.btn_swap)
        lang_bar.add_widget(self.btn_tgt)

        # 2. ტექსტური არე
        inp_kwargs = {
            "hint_text": "ჩაწერეთ ტექსტი...",
            "size_hint_y": 0.25,
            "multiline": True,
            "background_color": (0.14, 0.08, 0.22, 1),
            "foreground_color": (1, 1, 1, 1),
            "font_size": "15sp"
        }
        if FONT_PATH: inp_kwargs["font_name"] = FONT_PATH
        self.txt_in = TextInput(**inp_kwargs)
        self.txt_in.bind(text=lambda instance, val: self.translate_text_live(val))

        out_kwargs = {
            "hint_text": "თარგმანი გამოჩნდება აქ...",
            "size_hint_y": 0.25,
            "readonly": True,
            "multiline": True,
            "background_color": (0.14, 0.08, 0.22, 1),
            "foreground_color": (0.85, 0.8, 1, 1),
            "font_size": "15sp"
        }
        if FONT_PATH: out_kwargs["font_name"] = FONT_PATH
        self.txt_out = TextInput(**out_kwargs)

        # 3. Real-Time ხმოვანი დიალოგის ღილაკი
        self.btn_realtime = Button(
            text="🎙️ უწყვეტი Real-Time დიალოგი (Live)",
            size_hint_y=None,
            height="50dp",
            background_normal="",
            background_color=(0.48, 0.18, 0.65, 1),
            color=(1, 1, 1, 1),
            bold=True
        )
        if FONT_PATH: self.btn_realtime.font_name = FONT_PATH
        self.btn_realtime.bind(on_release=lambda x: self.open_realtime_dialog())

        # 4. სტატუსის ბარი (Offline/Online ინდიკატორი)
        status_text = "🟢 Online AI Engine" if GEMINI_API_KEY else "🟡 Offline ONNX Engine Mode"
        self.lbl_status = Label(text=status_text, size_hint_y=None, height="25dp", font_size="11sp", color=(0.7, 0.7, 0.7, 1))

        layout.add_widget(lang_bar)
        layout.add_widget(self.txt_in)
        layout.add_widget(self.txt_out)
        layout.add_widget(self.btn_realtime)
        layout.add_widget(self.lbl_status)

        self.add_widget(layout)

    def _update_bg(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    # ---------------------------------------------------------
    # ონლაინ / ოფლაინ ჰიბრიდული თარგმნა
    # ---------------------------------------------------------
    def translate_text_live(self, text):
        text = text.strip()
        if not text:
            self.txt_out.text = ""
            return

        def _worker():
            translated = None
            
            # 1. მცდელობა: Online Translation
            try:
                ctx = ssl._create_unverified_context()
                q = urllib.parse.quote(text)
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={self.source_lang}&tl={self.target_lang}&dt=t&q={q}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=3, context=ctx) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        translated = "".join([i[0] for i in data[0] if i and i[0]])
            except Exception:
                translated = None

            # 2. Fallback: Offline ONNX AI Engine
            if not translated:
                translated = self.offline_engine.translate_offline(text, self.source_lang, self.target_lang)
                if translated:
                    translated = f"[Offline AI]: {translated}"

            # 3. UI განახლება
            final_res = translated if translated else "თარგმნა ვერ მოხერხდა (Offline Model Not Found)"
            Clock.schedule_once(lambda dt: setattr(self.txt_out, 'text', final_res))

        threading.Thread(target=_worker, daemon=True).start()

    # ---------------------------------------------------------
    # Real-Time Voice Translation (უწყვეტი რეჟიმი)
    # ---------------------------------------------------------
    def open_realtime_dialog(self):
        trigger_haptic_feedback()
        layout = BoxLayout(orientation="vertical", padding=10, spacing=8)

        scroll = ScrollView(size_hint_y=0.85)
        self.chat_container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=8)
        self.chat_container.bind(minimum_height=self.chat_container.setter('height'))
        scroll.add_widget(self.chat_container)

        btn_toggle = Button(
            text="🛑 შეჩერება" if self.is_realtime_listening else "▶️ მოსმენის დაწყება",
            size_hint_y=None,
            height="45dp",
            background_normal="",
            background_color=(0.7, 0.2, 0.2, 1) if self.is_realtime_listening else (0.2, 0.6, 0.3, 1)
        )
        if FONT_PATH: btn_toggle.font_name = FONT_PATH

        popup = BasePopup(title="Real-Time ხმოვანი თარჯიმანი", content=layout, size_hint=(0.95, 0.9))

        def toggle_listen(instance):
            self.is_realtime_listening = not self.is_realtime_listening
            if self.is_realtime_listening:
                btn_toggle.text = "🛑 შეჩერება"
                btn_toggle.background_color = (0.7, 0.2, 0.2, 1)
                self.start_realtime_loop()
            else:
                btn_toggle.text = "▶️ მოსმენის დაწყება"
                btn_toggle.background_color = (0.2, 0.6, 0.3, 1)

        btn_toggle.bind(on_release=toggle_listen)
        layout.add_widget(scroll)
        layout.add_widget(btn_toggle)
        popup.open()

    def start_realtime_loop(self):
        """
        უწყვეტი მოსმენის ნაკადი (Voice Activity Detection Loop)
        """
        def _loop():
            while self.is_realtime_listening:
                # პლატფორმის მიხედვით ხმის ჩაწერა
                if platform == "android":
                    # Android Native Speech Capture Trigger
                    Clock.schedule_once(lambda dt: self._trigger_native_stt())
                    time.sleep(4)  # მოსმენის ციკლის ინტერვალი
                else:
                    # Desktop (Windows/macOS/Linux) ხმის სიმულაცია / PyAudio integration Point
                    time.sleep(3)

        self.realtime_thread = threading.Thread(target=_loop, daemon=True)
        self.realtime_thread.start()

    def _trigger_native_stt(self):
        if platform == "android":
            try:
                from jnius import autoclass
                Intent = autoclass("android.content.Intent")
                RecognizerIntent = autoclass("android.speech.RecognizerIntent")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, self.target_lang if self.source_lang == "auto" else self.source_lang)
                
                PythonActivity.mActivity.startActivityForResult(intent, 2001)
            except Exception as e:
                print(f"STT Error: {e}")

    def append_chat_message(self, speaker, text, translated):
        if not self.chat_container:
            return

        box = BoxLayout(orientation="vertical", size_hint_y=None, padding=5, spacing=2)
        box.bind(minimum_height=box.setter('height'))

        lbl_in = Label(text=f"🗣️ {speaker}: {text}", size_hint_y=None, color=(0.8, 0.8, 0.8, 1), font_size="13sp")
        if FONT_PATH: lbl_in.font_name = FONT_PATH
        lbl_in.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))

        lbl_out = Label(text=f"🌐 {translated}", size_hint_y=None, color=(0.4, 1, 0.5, 1), bold=True, font_size="14sp")
        if FONT_PATH: lbl_out.font_name = FONT_PATH
        lbl_out.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))

        box.add_widget(lbl_in)
        box.add_widget(lbl_out)
        self.chat_container.add_widget(box)

    def select_lang(self, mode):
        # ენის არჩევის ლოგიკა
        pass

    def swap_langs(self):
        trigger_haptic_feedback()
        if self.source_lang != "auto":
            self.source_lang, self.target_lang = self.target_lang, self.source_lang
            self.btn_src.text, self.btn_tgt.text = self.btn_tgt.text, self.btn_src.text

# ---------------------------------------------------------
# აპლიკაციის გაშვება
# ---------------------------------------------------------
class LingoLensApp(App):
    def build(self):
        request_system_permissions()
        sm = ScreenManager()
        self.main_screen = LingoLensMainScreen(name="main")
        sm.add_widget(self.main_screen)
        return sm

    def on_start(self):
        # Android Activity Result-ის მიღება Real-Time ხმოვანი შეყვანისთვის
        if platform == "android":
            try:
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")

                class SpeechListener:
                    def __init__(self, app_inst):
                        self.app = app_inst

                    def onActivityResult(self, requestCode, resultCode, intent):
                        if resultCode == -1 and requestCode == 2001 and intent:
                            RecognizerIntent = autoclass("android.speech.RecognizerIntent")
                            results = intent.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                            if results and results.size() > 0:
                                recognized_text = results.get(0)
                                Clock.schedule_once(lambda dt: self.app.main_screen.translate_text_live(recognized_text))

                self.listener = SpeechListener(self)
                PythonActivity.mActivity.bind(on_activity_result=self.listener.onActivityResult)
            except Exception as e:
                print(f"Android Activity Binding Error: {e}")

if __name__ == "__main__":
    LingoLensApp().run()
