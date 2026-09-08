import os
import sys
import json
import ssl
import sqlite3
import threading
import urllib.request
import urllib.parse

from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.graphics import Color, Rectangle
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup

# ლოკალური მოდულების იმპორტი
from languages import WORLD_LANGUAGES

try:
    from offline_engine import OfflineTranslatorEngine, HAS_ONNX
except ImportError:
    HAS_ONNX = False
    class OfflineTranslatorEngine:
        def __init__(self):
            self.is_loaded = False
        def translate_offline(self, text, src_lang, tgt_lang):
            return None

try:
    from plyer import share
    HAS_PLYER_SHARE = True
except ImportError:
    HAS_PLYER_SHARE = False

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None

# ---------------------------------------------------------
# 1. SQLite Database Manager
# ---------------------------------------------------------
class DatabaseManager:
    def __init__(self, db_path="lingolens.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    src_text TEXT NOT NULL,
                    tgt_text TEXT NOT NULL,
                    src_lang TEXT,
                    tgt_lang TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    src_text TEXT UNIQUE NOT NULL,
                    tgt_text TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_history(self, src, tgt, src_l, tgt_l):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute(
                    "INSERT INTO history (src_text, tgt_text, src_lang, tgt_lang) VALUES (?, ?, ?, ?)",
                    (src, tgt, src_l, tgt_l)
                )
                conn.commit()
        except Exception as e:
            print(f"[DB Error] History insert: {e}")

    def add_favorite(self, src, tgt):
        try:
            with self._get_connection() as conn:
                conn.cursor().execute("INSERT OR REPLACE INTO favorites (src_text, tgt_text) VALUES (?, ?)", (src, tgt))
                conn.commit()
                return True
        except Exception as e:
            print(f"[DB Error] Fav insert: {e}")
            return False

    def get_favorites(self):
        with self._get_connection() as conn:
            return conn.cursor().execute("SELECT src_text, tgt_text FROM favorites").fetchall()

# ---------------------------------------------------------
# 2. Native Android Overlay / Floating Window Helpers
# ---------------------------------------------------------
def trigger_haptic_feedback():
    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            vibrator = PythonActivity.mActivity.getSystemService(Context.VIBRATION_SERVICE)
            if vibrator and vibrator.hasVibrator():
                vibrator.vibrate(40)
        except Exception:
            pass

def check_and_request_overlay_permission():
    """ამოწმებს აქვს თუ არა აპლიკაციას სხვა აპლიკაციებზე გამოჩენის ნებართვა (Draw over other apps)"""
    if platform == "android":
        try:
            from jnius import autoclass
            Settings = autoclass("android.provider.Settings")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity

            if not Settings.canDrawOverlays(activity):
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                intent = Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse(f"package:{activity.getPackageName()}")
                )
                activity.startActivity(intent)
                return False
            return True
        except Exception as e:
            print(f"[Overlay Permission Error]: {e}")
            return True
    return True

def start_floating_window_service():
    """Android-ზე WindowManager-ით მცურავი ფანჯრის შექმნის ნატიური ლოგიკა"""
    if platform == "android":
        if not check_and_request_overlay_permission():
            return False

        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            WindowManager = autoclass("android.view.WindowManager")
            LayoutParams = autoclass("android.view.WindowManager$LayoutParams")
            PixelFormat = autoclass("android.graphics.PixelFormat")
            TextView = autoclass("android.widget.TextView")
            Color = autoclass("android.graphics.Color")
            Gravity = autoclass("android.view.Gravity")

            activity = PythonActivity.mActivity
            wm = activity.getSystemService(Context.WINDOW_SERVICE)

            # WindowType დაყენება ვერსიის მიხედვით
            Build = autoclass("android.os.Build$VERSION")
            if Build.SDK_INT >= 26:
                LAYOUT_TYPE = LayoutParams.TYPE_APPLICATION_OVERLAY
            else:
                LAYOUT_TYPE = LayoutParams.TYPE_PHONE

            params = LayoutParams(
                LayoutParams.WRAP_CONTENT,
                LayoutParams.WRAP_CONTENT,
                LAYOUT_TYPE,
                LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT
            )
            params.gravity = Gravity.TOP | Gravity.LEFT
            params.x = 100
            params.y = 300

            # მცურავი ვიჯეტი
            floating_tv = TextView(activity)
            floating_tv.setText("🔍 LingoLens Quick Translate")
            floating_tv.setTextColor(Color.WHITE)
            floating_tv.setBackgroundColor(Color.parseColor("#CC1E102A"))
            floating_tv.setPadding(25, 25, 25, 25)

            wm.addView(floating_tv, params)
            return True
        except Exception as e:
            print(f"[Floating Window Launch Error]: {e}")
            return False
    return False

def native_share_text(text):
    if not text:
        return
    trigger_haptic_feedback()

    if platform == "android":
        try:
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            String = autoclass('java.lang.String')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')

            send_intent = Intent()
            send_intent.setAction(Intent.ACTION_SEND)
            send_intent.putExtra(Intent.EXTRA_TEXT, String(text))
            send_intent.setType("text/plain")

            chooser = Intent.createChooser(send_intent, String("გააზიარეთ ტექსტი..."))
            PythonActivity.mActivity.startActivity(chooser)
            return
        except Exception as e:
            print(f"[Native Android Share Error]: {e}")

    if HAS_PLYER_SHARE:
        try:
            share.share(title="LingoLens Translation", text=text)
        except Exception as e:
            print(f"[Plyer Share Error]: {e}")

def native_tts_speak(text, lang="ka", rate=1.0):
    if platform == "android":
        try:
            from jnius import autoclass
            TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
            Locale = autoclass("java.util.Locale")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            
            def on_init(status):
                if status == TextToSpeech.SUCCESS:
                    tts.setLanguage(Locale(lang))
                    tts.setSpeechRate(rate)
                    tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            
            tts = TextToSpeech(PythonActivity.mActivity, TextToSpeech.OnInitListener())
        except Exception as e:
            print(f"[TTS Error]: {e}")

# ---------------------------------------------------------
# 3. UI Popups: Searchable Language Selector & Floating In-App Window
# ---------------------------------------------------------
class LanguageSelectPopup(Popup):
    def __init__(self, callback, include_auto=True, **kwargs):
        super().__init__(**kwargs)
        self.title = "აირჩიეთ ენა (100+ ენა)"
        if FONT_PATH: self.title_font = FONT_PATH
        self.size_hint = (0.9, 0.85)
        self.callback = callback
        self.include_auto = include_auto

        layout = BoxLayout(orientation="vertical", padding=10, spacing=8)
        self.search_input = TextInput(
            hint_text="🔍 ჩაწერეთ ენის დასახელება...",
            size_hint_y=None, height="45dp",
            multiline=False,
            background_color=(0.18, 0.12, 0.28, 1),
            foreground_color=(1, 1, 1, 1)
        )
        if FONT_PATH: self.search_input.font_name = FONT_PATH
        self.search_input.bind(text=self.filter_languages)

        scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=4, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)

        layout.add_widget(self.search_input)
        layout.add_widget(scroll)
        self.content = layout

        self.populate_list(WORLD_LANGUAGES)

    def populate_list(self, lang_dict):
        self.grid.clear_widgets()
        for name, code in lang_dict.items():
            if not self.include_auto and code == "auto":
                continue
            btn = Button(
                text=name, size_hint_y=None, height="42dp",
                background_normal="", background_color=(0.25, 0.15, 0.38, 1),
                color=(1, 1, 1, 1)
            )
            if FONT_PATH: btn.font_name = FONT_PATH
            btn.bind(on_release=lambda x, n=name, c=code: self.select_language(n, c))
            self.grid.add_widget(btn)

    def filter_languages(self, instance, text):
        query = text.strip().lower()
        if not query:
            self.populate_list(WORLD_LANGUAGES)
            return
        filtered = {n: c for n, c in WORLD_LANGUAGES.items() if query in n.lower()}
        self.populate_list(filtered)

    def select_language(self, name, code):
        self.callback(name, code)
        self.dismiss()

class InAppFloatingWidget(Popup):
    """Kivy-ს შიდა მცურავი/სწრაფი ფანჯარა აპლიკაციის შიგნით სარგებლობისთვის"""
    def __init__(self, main_screen, **kwargs):
        super().__init__(**kwargs)
        self.title = "🪟 მცურავი სწრაფი თარჯიმანი"
        if FONT_PATH: self.title_font = FONT_PATH
        self.size_hint = (0.85, 0.45)
        self.auto_dismiss = False
        self.main_screen = main_screen

        layout = BoxLayout(orientation="vertical", padding=8, spacing=6)
        
        self.in_text = TextInput(
            hint_text="ჩაწერეთ ტექსტი სწრაფი თარგმნისთვის...",
            size_hint_y=0.4, multiline=True,
            background_color=(0.18, 0.12, 0.28, 1),
            foreground_color=(1, 1, 1, 1)
        )
        self.out_label = Label(
            text="თარგმანი გამოჩნდება აქ",
            size_hint_y=0.4, color=(0.85, 0.8, 1, 1)
        )
        if FONT_PATH:
            self.in_text.font_name = FONT_PATH
            self.out_label.font_name = FONT_PATH

        self.in_text.bind(text=self.quick_translate)

        btn_close = Button(
            text="დახურვა", size_hint_y=0.2,
            background_normal="", background_color=(0.7, 0.2, 0.2, 1)
        )
        if FONT_PATH: btn_close.font_name = FONT_PATH
        btn_close.bind(on_release=self.dismiss)

        layout.add_widget(self.in_text)
        layout.add_widget(self.out_label)
        layout.add_widget(btn_close)
        self.content = layout

    def quick_translate(self, instance, text):
        if text.strip():
            self.main_screen.execute_translation(text, callback=self.update_result)
        else:
            self.out_label.text = ""

    def update_result(self, src, res):
        self.out_label.text = res

# ---------------------------------------------------------
# 4. Main LingoLens Interface Screen
# ---------------------------------------------------------
class LingoLensMainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.offline_engine = OfflineTranslatorEngine()
        
        self.source_lang = "auto"
        self.target_lang = "ka"
        self.tts_speed = 1.0
        self.debounce_event = None

        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(orientation="vertical", padding=10, spacing=8)
        with layout.canvas.before:
            Color(0.06, 0.03, 0.10, 1)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._update_bg, pos=self._update_bg)

        # 1. Top Language Selection Bar
        lang_bar = BoxLayout(size_hint_y=None, height="45dp", spacing=6)
        btn_style = {"background_normal": "", "background_color": (0.22, 0.12, 0.35, 1), "color": (1, 1, 1, 1)}

        self.btn_src = Button(text="ავტოდაჭერა (Auto)", size_hint_x=0.42, **btn_style)
        self.btn_swap = Button(text="⇄", size_hint_x=0.16, bold=True, **btn_style)
        self.btn_tgt = Button(text="ქართული", size_hint_x=0.42, **btn_style)

        if FONT_PATH:
            self.btn_src.font_name = FONT_PATH
            self.btn_tgt.font_name = FONT_PATH

        self.btn_src.bind(on_release=lambda x: self.open_lang_picker("source"))
        self.btn_swap.bind(on_release=lambda x: self.swap_languages())
        self.btn_tgt.bind(on_release=lambda x: self.open_lang_picker("target"))

        lang_bar.add_widget(self.btn_src)
        lang_bar.add_widget(self.btn_swap)
        lang_bar.add_widget(self.btn_tgt)

        # 2. Text Inputs Panel
        self.txt_in = TextInput(
            hint_text="ჩაწერეთ ტექსტი...", size_hint_y=0.20,
            multiline=True, background_color=(0.14, 0.08, 0.22, 1),
            foreground_color=(1, 1, 1, 1), font_size="15sp"
        )
        self.txt_out = TextInput(
            hint_text="თარგმანი გამოჩნდება აქ...", size_hint_y=0.20,
            readonly=True, multiline=True, background_color=(0.14, 0.08, 0.22, 1),
            foreground_color=(0.85, 0.8, 1, 1), font_size="15sp"
        )
        if FONT_PATH:
            self.txt_in.font_name = FONT_PATH
            self.txt_out.font_name = FONT_PATH

        self.txt_in.bind(text=self.on_input_text_change)

        # 3. Quick Action Toolbar
        action_bar = BoxLayout(size_hint_y=None, height="40dp", spacing=4)
        btn_act = {"background_normal": "", "background_color": (0.30, 0.18, 0.45, 1), "color": (1, 1, 1, 1)}

        btn_tts = Button(text="🔊", size_hint_x=0.18, **btn_act)
        btn_copy = Button(text="📋 კოპირება", size_hint_x=0.27, **btn_act)
        btn_share = Button(text="🔗 გაზიარება", size_hint_x=0.27, **btn_act)
        btn_fav = Button(text="⭐", size_hint_x=0.14, **btn_act)
        btn_think = Button(text="🧠", size_hint_x=0.14, **btn_act)

        if FONT_PATH:
            btn_tts.font_name = btn_copy.font_name = btn_share.font_name = btn_fav.font_name = btn_think.font_name = FONT_PATH

        btn_tts.bind(on_release=lambda x: native_tts_speak(self.txt_out.text, self.target_lang, self.tts_speed))
        btn_copy.bind(on_release=lambda x: self.copy_to_clipboard())
        btn_share.bind(on_release=lambda x: native_share_text(self.txt_out.text))
        btn_fav.bind(on_release=lambda x: self.save_favorite())
        btn_think.bind(on_release=lambda x: self.open_deep_think())

        action_bar.add_widget(btn_tts)
        action_bar.add_widget(btn_copy)
        action_bar.add_widget(btn_share)
        action_bar.add_widget(btn_fav)
        action_bar.add_widget(btn_think)

        # 4. Floating Window & Modes Launcher
        mode_bar = BoxLayout(size_hint_y=None, height="48dp", spacing=6)
        btn_float = Button(text="🪟 მცურავი ფანჯარა", background_normal="", background_color=(0.18, 0.45, 0.65, 1), bold=True)
        btn_realtime = Button(text="🎙️ Real-Time", background_normal="", background_color=(0.5, 0.18, 0.65, 1), bold=True)
        btn_quiz = Button(text="🎓 ქვიზი", background_normal="", background_color=(0.2, 0.5, 0.4, 1), bold=True)

        if FONT_PATH:
            btn_float.font_name = btn_realtime.font_name = btn_quiz.font_name = FONT_PATH

        btn_float.bind(on_release=lambda x: self.toggle_floating_window())
        btn_realtime.bind(on_release=lambda x: self.open_realtime_mode())
        btn_quiz.bind(on_release=lambda x: self.open_quiz_mode())

        mode_bar.add_widget(btn_float)
        mode_bar.add_widget(btn_realtime)
        mode_bar.add_widget(btn_quiz)

        # 5. Status Engine Indicator
        status_text = "🟢 Hybrid Online AI Engine Active" if HAS_ONNX else "🌐 Standard Network Mode"
        self.lbl_status = Label(text=status_text, size_hint_y=None, height="20dp", font_size="11sp", color=(0.6, 0.6, 0.6, 1))

        # Add to Layout
        layout.add_widget(lang_bar)
        layout.add_widget(self.txt_in)
        layout.add_widget(action_bar)
        layout.add_widget(self.txt_out)
        layout.add_widget(mode_bar)
        layout.add_widget(self.lbl_status)

        self.add_widget(layout)

    def _update_bg(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    # ---------------------------------------------------------
    # Floating Window Handler
    # ---------------------------------------------------------
    def toggle_floating_window(self):
        trigger_haptic_feedback()
        if platform == "android":
            success = start_floating_window_service()
            if not success:
                # Fallback თუ სისტემური Overlay-ის ნებართვა არ არის მიცემული
                InAppFloatingWidget(main_screen=self).open()
        else:
            InAppFloatingWidget(main_screen=self).open()

    # ---------------------------------------------------------
    # Translation Logic with Debounce
    # ---------------------------------------------------------
    def on_input_text_change(self, instance, value):
        if self.debounce_event:
            self.debounce_event.cancel()
        self.debounce_event = Clock.schedule_once(lambda dt: self.execute_translation(value), 0.5)

    def execute_translation(self, text, callback=None):
        text = text.strip()
        if not text:
            if callback:
                callback(text, "")
            else:
                self.txt_out.text = ""
            return

        def _worker():
            translated = None
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

            if not translated and getattr(self.offline_engine, 'is_loaded', False):
                translated = self.offline_engine.translate_offline(text, self.source_lang, self.target_lang)
                if translated:
                    translated = f"[Offline AI]: {translated}"

            res_final = translated if translated else "თარგმნა ვერ მოხერხდა"
            
            if callback:
                Clock.schedule_once(lambda dt: callback(text, res_final))
            else:
                Clock.schedule_once(lambda dt: self._update_out_ui(text, res_final))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_out_ui(self, src_text, tgt_text):
        self.txt_out.text = tgt_text
        if tgt_text and not tgt_text.startswith("[Offline AI] Error"):
            self.db.add_history(src_text, tgt_text, self.source_lang, self.target_lang)

    def open_lang_picker(self, mode):
        trigger_haptic_feedback()
        include_auto = (mode == "source")
        def on_selected(name, code):
            if mode == "source":
                self.source_lang = code
                self.btn_src.text = name
            else:
                self.target_lang = code
                self.btn_tgt.text = name
            if self.txt_in.text.strip():
                self.execute_translation(self.txt_in.text)
        LanguageSelectPopup(callback=on_selected, include_auto=include_auto).open()

    def swap_languages(self):
        trigger_haptic_feedback()
        if self.source_lang != "auto":
            self.source_lang, self.target_lang = self.target_lang, self.source_lang
            self.btn_src.text, self.btn_tgt.text = self.btn_tgt.text, self.btn_src.text
            if self.txt_in.text.strip():
                self.execute_translation(self.txt_in.text)

    def copy_to_clipboard(self):
        if self.txt_out.text:
            Clipboard.copy(self.txt_out.text)
            trigger_haptic_feedback()

    def save_favorite(self):
        if self.txt_in.text and self.txt_out.text:
            if self.db.add_favorite(self.txt_in.text, self.txt_out.text):
                trigger_haptic_feedback()

    def open_deep_think(self):
        text = self.txt_in.text.strip()
        if not text:
            return
        words = len(text.split())
        chars = len(text)
        info = f"📊 ტექსტის ანალიზი (Deep Think):\n\n• სიტყვები: {words}\n• სიმბოლოები: {chars}\n• ენა: {self.source_lang} ➔ {self.target_lang}"
        p = Popup(title="Deep Think Analysis", content=Label(text=info), size_hint=(0.8, 0.5))
        p.open()

    def open_realtime_mode(self):
        p = Popup(title="Real-Time დიალოგი", content=Label(text="🎙️ უწყვეტი მოსმენის რეჟიმი აქტიურია..."), size_hint=(0.85, 0.6))
        p.open()

    def open_quiz_mode(self):
        favs = self.db.get_favorites()
        msg = f"📚 ფავორიტების ბაზაშია {len(favs)} სიტყვა." if favs else "❌ ფავორიტები ცარიელია. ჯერ დაამატეთ სიტყვები!"
        p = Popup(title="ქვიზის რეჟიმი", content=Label(text=msg), size_hint=(0.8, 0.5))
        p.open()

# ---------------------------------------------------------
# 5. Application Entry Point
# ---------------------------------------------------------
class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro"
        sm = ScreenManager()
        sm.add_widget(LingoLensMainScreen(name="main"))
        return sm

if __name__ == "__main__":
    LingoLensApp().run()
