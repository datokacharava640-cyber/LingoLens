import os
import json
import base64
import threading
import urllib.request
import urllib.parse

from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup

# API Key იმპორტი config.py-დან
try:
    from config import GEMINI_API_KEY
except ImportError:
    GEMINI_API_KEY = ""

# ---------------------------------------------------------
# 0. აპლიკაციის მეტამონაცემები
# ---------------------------------------------------------
APP_NAME = "LingoLens Ultra Pro"
CURRENT_VERSION = "1.1.0"
AUTHOR_NAME = "Dato Kacharava"
CREATION_DATE = "2026-09-08"
LICENSE_NAME = "EISI / MIT Open License"

UPDATE_CHECK_URL = "https://raw.githubusercontent.com/example/lingolens/main/version.json"

APP_CREDITS_TEXT = (
    f"{APP_NAME} v{CURRENT_VERSION} | შექმნის თარიღი: {CREATION_DATE}\n"
    f"ავტორი: {AUTHOR_NAME} | ლიცენზია: {LICENSE_NAME}\n"
    "Powered by Google Translate & Gemini Vision API"
)

# ---------------------------------------------------------
# 1. ფონტის ჩატვირთვა
# ---------------------------------------------------------
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None

# ---------------------------------------------------------
# 2. ენების სია
# ---------------------------------------------------------
LANGUAGES = {
    "ავტოდაჭერა": "auto",
    "ქართული": "ka",
    "ინგლისური": "en",
    "რუსული": "ru",
    "გერმანული": "de",
    "ფრანგული": "fr",
    "ესპანური": "es",
    "იტალიური": "it",
    "თურქული": "tr",
    "ჩინური (გამარტივებული)": "zh-CN",
    "ჩინური (ტრადიციული)": "zh-TW",
    "იაპონური": "ja",
    "კორეული": "ko",
    "არაბული": "ar",
    "უკრაინული": "uk",
    "პოლონური": "pl",
    "ბერძნული": "el",
    "ჰოლანდიური": "nl",
    "პორტუგალიური": "pt",
    "შვედური": "sv",
    "ნორვეგიული": "no",
    "დანიური": "da",
    "ფინური": "fi",
    "ჩეხური": "cs",
    "უნგრული": "hu",
    "რუმინული": "ro",
    "ბულგარული": "bg",
    "ებრაული": "he",
    "ინდონეზიური": "id",
    "ვიეტნამური": "vi",
    "ტაილანდური": "th",
    "ჰინდი": "hi",
    "ბენგალური": "bn",
    "აზერბაიჯანული": "az",
    "სომხური": "hy",
    "ყაზახური": "kk",
    "უზბეკური": "uz"
}

# ---------------------------------------------------------
# 3. Android ნებართვები და ვიბრაცია
# ---------------------------------------------------------
def request_android_permissions():
    if platform == "android":
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.RECORD_AUDIO,
                Permission.CAMERA,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.VIBRATE
            ])
        except Exception as e:
            print(f"Permission error: {e}")

def trigger_vibration():
    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            activity = PythonActivity.mActivity
            vibrator = activity.getSystemService(Context.VIBRATION_SERVICE)
            if vibrator and vibrator.hasVibrator():
                vibrator.vibrate(50)
        except Exception as e:
            print(f"Vibration error: {e}")

# ---------------------------------------------------------
# 4. ლოკალური ბაზა
# ---------------------------------------------------------
class LocalDB:
    def __init__(self):
        self.fav_file = "favorites.json"
        self.hist_file = "history.json"
        self.init_db()

    def init_db(self):
        if not os.path.exists(self.fav_file):
            with open(self.fav_file, "w", encoding="utf-8") as f:
                json.dump([], f)
        if not os.path.exists(self.hist_file):
            with open(self.hist_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def add_favorite(self, src, tgt, orig, trans):
        favs = self.get_favorites()
        item = [orig, trans, src, tgt]
        if item not in favs:
            favs.append(item)
            with open(self.fav_file, "w", encoding="utf-8") as f:
                json.dump(favs, f, ensure_ascii=False)
            return True
        return False

    def get_favorites(self):
        try:
            with open(self.fav_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def add_history(self, src, tgt, orig, trans):
        hist = self.get_history()
        hist.insert(0, [orig, trans, src, tgt])
        with open(self.hist_file, "w", encoding="utf-8") as f:
            json.dump(hist[:50], f, ensure_ascii=False)

    def get_history(self):
        try:
            with open(self.hist_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def search_offline_cache(self, src, tgt, text):
        hist = self.get_history()
        for item in hist:
            if item[0].lower() == text.lower() and item[2] == src and item[3] == tgt:
                return item[1]
        return None

db = LocalDB()

# ---------------------------------------------------------
# 5. FontPopup
# ---------------------------------------------------------
class FontPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if FONT_PATH:
            self.title_font = FONT_PATH

# ---------------------------------------------------------
# 6. MainScreen
# ---------------------------------------------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "auto"
        self.target_lang = "ka"
        self._debounce_event = None
        self.photo_path = None

        self._build_ui()
        Clock.schedule_once(lambda dt: self.check_for_updates(silent=True), 3)

    def _build_ui(self):
        main_layout = BoxLayout(orientation="vertical", padding=10, spacing=8)

        lang_layout = BoxLayout(size_hint_y=None, height="45dp", spacing=5)
        
        btn_src_kwargs = {"text": "ავტოდაჭერა", "size_hint_x": 0.4}
        if FONT_PATH: btn_src_kwargs["font_name"] = FONT_PATH
        self.btn_src = Button(**btn_src_kwargs)
        self.btn_src.bind(on_release=lambda x: self.open_language_selector("source"))

        btn_swap_kwargs = {"text": "<=>", "size_hint_x": 0.2}
        if FONT_PATH: btn_swap_kwargs["font_name"] = FONT_PATH
        self.btn_swap = Button(**btn_swap_kwargs)
        self.btn_swap.bind(on_release=lambda x: self.swap_languages())

        btn_tgt_kwargs = {"text": "ქართული", "size_hint_x": 0.4}
        if FONT_PATH: btn_tgt_kwargs["font_name"] = FONT_PATH
        self.btn_tgt = Button(**btn_tgt_kwargs)
        self.btn_tgt.bind(on_release=lambda x: self.open_language_selector("target"))

        lang_layout.add_widget(self.btn_src)
        lang_layout.add_widget(self.btn_swap)
        lang_layout.add_widget(self.btn_tgt)

        inp_kwargs = {
            "hint_text": "ჩაწერეთ, ჩასვით ტექსტი ან გამოიყენეთ კამერა...",
            "size_hint_y": 0.25,
            "multiline": True,
            "font_size": "16sp"
        }
        if FONT_PATH: inp_kwargs["font_name"] = FONT_PATH
        self.input_text = TextInput(**inp_kwargs)
        self.input_text.bind(text=lambda instance, val: self.on_live_translate(val))

        ctrl_layout = BoxLayout(size_hint_y=None, height="40dp", spacing=5)
        
        btn_stt_kwargs = {"text": "ხმა", "size_hint_x": 0.25}
        if FONT_PATH: btn_stt_kwargs["font_name"] = FONT_PATH
        btn_stt = Button(**btn_stt_kwargs)
        btn_stt.bind(on_release=lambda x: self.start_speech_to_text(self.source_lang))

        btn_cam_kwargs = {"text": "კამერა", "size_hint_x": 0.25}
        if FONT_PATH: btn_cam_kwargs["font_name"] = FONT_PATH
        btn_cam = Button(**btn_cam_kwargs)
        btn_cam.bind(on_release=lambda x: self.open_camera_translator())

        btn_clr_kwargs = {"text": "გასუფთავება", "size_hint_x": 0.25}
        if FONT_PATH: btn_clr_kwargs["font_name"] = FONT_PATH
        btn_clr = Button(**btn_clr_kwargs)
        btn_clr.bind(on_release=lambda x: self.clear_input_text())

        btn_int_kwargs = {"text": "თარჯიმანი", "size_hint_x": 0.25}
        if FONT_PATH: btn_int_kwargs["font_name"] = FONT_PATH
        btn_int = Button(**btn_int_kwargs)
        btn_int.bind(on_release=lambda x: self.open_interpreter_mode())

        ctrl_layout.add_widget(btn_stt)
        ctrl_layout.add_widget(btn_cam)
        ctrl_layout.add_widget(btn_clr)
        ctrl_layout.add_widget(btn_int)

        out_kwargs = {
            "hint_text": "თარგმანი გამოჩნდება აქ...",
            "size_hint_y": 0.25,
            "multiline": True,
            "readonly": True,
            "font_size": "16sp"
        }
        if FONT_PATH: out_kwargs["font_name"] = FONT_PATH
        self.output_text = TextInput(**out_kwargs)

        out_ctrl = BoxLayout(size_hint_y=None, height="40dp", spacing=5)
        
        btn_tts_kwargs = {"text": "წაკითხვა"}
        if FONT_PATH: btn_tts_kwargs["font_name"] = FONT_PATH
        btn_tts = Button(**btn_tts_kwargs)
        btn_tts.bind(on_release=lambda x: self.speak_output_text())

        btn_copy_kwargs = {"text": "კოპირება"}
        if FONT_PATH: btn_copy_kwargs["font_name"] = FONT_PATH
        btn_copy = Button(**btn_copy_kwargs)
        btn_copy.bind(on_release=lambda x: self.copy_to_clipboard())

        btn_fav_kwargs = {"text": "ფავორიტი"}
        if FONT_PATH: btn_fav_kwargs["font_name"] = FONT_PATH
        btn_fav = Button(**btn_fav_kwargs)
        btn_fav.bind(on_release=lambda x: self.save_to_favorites())

        out_ctrl.add_widget(btn_tts)
        out_ctrl.add_widget(btn_copy)
        out_ctrl.add_widget(btn_fav)

        nav_layout = BoxLayout(size_hint_y=None, height="40dp", spacing=5)
        
        btn_dict_kwargs = {"text": "ლექსიკონი"}
        if FONT_PATH: btn_dict_kwargs["font_name"] = FONT_PATH
        btn_dict = Button(**btn_dict_kwargs)
        btn_dict.bind(on_release=lambda x: self.open_dictionary_hub())

        btn_quiz_kwargs = {"text": "ქვიზი"}
        if FONT_PATH: btn_quiz_kwargs["font_name"] = FONT_PATH
        btn_quiz = Button(**btn_quiz_kwargs)
        btn_quiz.bind(on_release=lambda x: self.open_quiz_mode())

        btn_file_kwargs = {"text": ".TXT ფაილი"}
        if FONT_PATH: btn_file_kwargs["font_name"] = FONT_PATH
        btn_file = Button(**btn_file_kwargs)
        btn_file.bind(on_release=lambda x: self.open_file_translator())

        nav_layout.add_widget(btn_dict)
        nav_layout.add_widget(btn_quiz)
        nav_layout.add_widget(btn_file)

        footer_kwargs = {
            "text": APP_CREDITS_TEXT,
            "size_hint_y": None,
            "height": "40dp",
            "font_size": "10sp",
            "halign": "center",
            "valign": "middle"
        }
        if FONT_PATH: footer_kwargs["font_name"] = FONT_PATH
        self.lbl_footer = Label(**footer_kwargs)
        self.lbl_footer.bind(size=self.lbl_footer.setter("text_size"))

        main_layout.add_widget(lang_layout)
        main_layout.add_widget(self.input_text)
        main_layout.add_widget(ctrl_layout)
        main_layout.add_widget(self.output_text)
        main_layout.add_widget(out_ctrl)
        main_layout.add_widget(nav_layout)
        main_layout.add_widget(self.lbl_footer)

        self.add_widget(main_layout)

    # ---------------------------------------------------------
    # 7. კამერა & Gemini Vision API
    # ---------------------------------------------------------
    def open_camera_translator(self):
        trigger_vibration()
        if platform == "android":
            try:
                from jnius import autoclass
                Intent = autoclass("android.provider.MediaStore").ACTION_IMAGE_CAPTURE
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                File = autoclass("java.io.File")
                
                storage_dir = PythonActivity.mActivity.getExternalFilesDir(None)
                photo_file = File(storage_dir, "temp_lingolens.jpg")
                self.photo_path = photo_file.getAbsolutePath()

                # Uri / FileProvider თავსებადობა Android 10+
                FileProvider = autoclass("androidx.core.content.FileProvider")
                context = PythonActivity.mActivity.getApplicationContext()
                file_uri = FileProvider.getUriForFile(
                    context, 
                    context.getPackageName() + ".fileprovider", 
                    photo_file
                )

                intent = Intent
                intent.putExtra("output", file_uri)
                PythonActivity.mActivity.startActivityForResult(intent, 1003)
            except Exception as e:
                # Fallback ძველი Android ვერსიებისთვის
                try:
                    Uri = autoclass("android.net.Uri")
                    file_uri = Uri.fromFile(photo_file)
                    intent = Intent
                    intent.putExtra("output", file_uri)
                    PythonActivity.mActivity.startActivityForResult(intent, 1003)
                except Exception as ex:
                    self._show_simple_popup("კამერის ხარვეზი", f"კამერის ჩართვა ვერ მოხერხდა: {ex}")
        else:
            self._show_image_path_dialog()

    def _show_image_path_dialog(self):
        layout = BoxLayout(orientation="vertical", padding=10, spacing=8)
        inp_kwargs = {"hint_text": "შეიყვანეთ ფოტოს გზა...", "size_hint_y": None, "height": "40dp", "multiline": False}
        if FONT_PATH: inp_kwargs["font_name"] = FONT_PATH
        inp_path = TextInput(**inp_kwargs)

        btn_kwargs = {"text": "Gemini-თ ამოცნობა", "size_hint_y": None, "height": "45dp"}
        if FONT_PATH: btn_kwargs["font_name"] = FONT_PATH
        btn_process = Button(**btn_kwargs)

        popup = FontPopup(title="ფოტოს ჩატვირთვა (PC)", content=layout, size_hint=(0.85, 0.4))

        def process_image(instance):
            path = inp_path.text.strip()
            if os.path.exists(path):
                popup.dismiss()
                self.process_image_with_gemini(path)
            else:
                self._show_simple_popup("შეცდომა", "ფაილი ვერ მოიძებნა!")

        btn_process.bind(on_release=process_image)
        layout.add_widget(inp_path)
        layout.add_widget(btn_process)
        popup.open()

    def process_image_with_gemini(self, image_path):
        if not GEMINI_API_KEY:
            self._show_simple_popup("Gemini API", "API Key ვერ მოიძებნა config.py-ში.")
            return

        self.output_text.text = "მიმდინარეობს ფოტოს დამუშავება Gemini Vision AI-ით..."

        def _thread_target():
            try:
                with open(image_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')

                target_lang_name = self.btn_tgt.text
                prompt = (
                    f"1. Extract all text visible in this image accurately.\n"
                    f"2. Translate that text into {target_lang_name}.\n"
                    f"Return ONLY valid JSON with structure: {{\"original_text\": \"...\", \"translated_text\": \"...\"}}"
                )

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": base64_image
                                }
                            }
                        ]
                    }],
                    "generationConfig": {
                        "response_mime_type": "application/json"
                    }
                }

                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )

                with urllib.request.urlopen(req, timeout=20) as response:
                    if response.status == 200:
                        res_data = json.loads(response.read().decode('utf-8'))
                        content_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                        parsed_json = json.loads(content_text)

                        orig_text = parsed_json.get("original_text", "")
                        trans_text = parsed_json.get("translated_text", "")

                        Clock.schedule_once(
                            lambda dt: self._update_ui_after_gemini(orig_text, trans_text)
                        )
                    else:
                        Clock.schedule_once(
                            lambda dt: self._set_output_text("Gemini API შეცდომა")
                        )
            except Exception as e:
                Clock.schedule_once(
                    lambda dt: self._set_output_text(f"ფოტოს ამოცნობა ვერ მოხერხდა: {e}")
                )

        threading.Thread(target=_thread_target, daemon=True).start()

    def _update_ui_after_gemini(self, original, translated):
        self.input_text.text = original
        self.output_text.text = translated
        if original and translated:
            db.add_history(self.source_lang, self.target_lang, original, translated)

    # ---------------------------------------------------------
    # 8. თარგმნის ლოგიკა & STT/TTS
    # ---------------------------------------------------------
    def start_speech_to_text(self, lang_code):
        trigger_vibration()
        if platform == "android":
            try:
                from jnius import autoclass
                Intent = autoclass("android.content.Intent")
                RecognizerIntent = autoclass("android.speech.RecognizerIntent")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(
                    RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                    RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
                )
                if lang_code != "auto":
                    intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)

                PythonActivity.mActivity.startActivityForResult(intent, 1002)
            except Exception as e:
                self._show_simple_popup("STT ხარვეზი", f"ხმოვანი შეყვანა მიუწვდომელია: {e}")
        else:
            self._show_simple_popup("STT", "ხმოვანი შეყვანა მხარდაჭერილია მხოლოდ Android-ზე.")

    def on_live_translate(self, text):
        if self._debounce_event:
            self._debounce_event.cancel()

        text = text.strip()
        if not text:
            self.output_text.text = ""
            return

        cached_trans = db.search_offline_cache(self.source_lang, self.target_lang, text)
        if cached_trans:
            self.output_text.text = cached_trans
            return

        self._debounce_event = Clock.schedule_once(
            lambda dt: self._execute_translation(text), 0.5
        )

    def _execute_translation(self, text):
        def _thread_target():
            try:
                query_encoded = urllib.parse.quote(text)
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={self.source_lang}&tl={self.target_lang}&dt=t&q={query_encoded}"
                
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        raw_data = response.read().decode('utf-8')
                        data = json.loads(raw_data)
                        translated = "".join([item[0] for item in data[0] if item[0]])
                        Clock.schedule_once(
                            lambda dt: self._handle_translation_success(text, translated)
                        )
            except Exception:
                Clock.schedule_once(
                    lambda dt: self._set_output_text("ინტერნეტთან კავშირი არ არის / ქეში ვერ მოიძებნა")
                )

        threading.Thread(target=_thread_target, daemon=True).start()

    def _handle_translation_success(self, original, translated):
        if self.input_text.text.strip() == original.strip():
            self.output_text.text = translated
            db.add_history(self.source_lang, self.target_lang, original, translated)

    def _set_output_text(self, text):
        self.output_text.text = text

    def open_language_selector(self, mode):
        trigger_vibration()
        main_layout = BoxLayout(orientation="vertical", padding=10, spacing=8)
        search_input = TextInput(
            hint_text="ძებნა...",
            size_hint_y=None,
            height="40dp",
            multiline=False
        )
        if FONT_PATH: search_input.font_name = FONT_PATH

        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=5)
        box.bind(minimum_height=box.setter("height"))

        popup = FontPopup(title="ენის არჩევა", content=main_layout, size_hint=(0.9, 0.85))

        def populate_languages(filter_text=""):
            box.clear_widgets()
            for name, code in LANGUAGES.items():
                if mode == "target" and code == "auto":
                    continue
                if filter_text.lower() in name.lower() or filter_text.lower() in code.lower():
                    btn_kwargs = {
                        "text": f"{name} ({code})",
                        "size_hint_y": None,
                        "height": "42dp"
                    }
                    if FONT_PATH: btn_kwargs["font_name"] = FONT_PATH
                    btn = Button(**btn_kwargs)
                    btn.bind(
                        on_release=lambda instance, c=code, n=name: self._select_language(
                            mode, c, n, popup
                        )
                    )
                    box.add_widget(btn)

        search_input.bind(text=lambda instance, value: populate_languages(value))
        populate_languages()

        scroll.add_widget(box)
        main_layout.add_widget(search_input)
        main_layout.add_widget(scroll)
        popup.open()

    def _select_language(self, mode, code, name, popup):
        trigger_vibration()
        if mode == "source":
            self.source_lang = code
            self.btn_src.text = name
        else:
            self.target_lang = code
            self.btn_tgt.text = name
        popup.dismiss()
        self.on_live_translate(self.input_text.text)

    def swap_languages(self):
        trigger_vibration()
        if self.source_lang == "auto":
            self._show_simple_popup("შეცდომა", "ავტოდაჭერის რეჟიმში ენების გაცვლა შეუძლებელია.")
            return

        old_src_code, old_src_text = self.source_lang, self.btn_src.text
        self.source_lang, self.btn_src.text = self.target_lang, self.btn_tgt.text
        self.target_lang, self.btn_tgt.text = old_src_code, old_src_text

        in_text, out_text = self.input_text.text, self.output_text.text
        self.input_text.text, self.output_text.text = out_text, in_text

    def speak_output_text(self):
        trigger_vibration()
        text = self.output_text.text.strip()
        if not text:
            return

        if platform == "android":
            try:
                from jnius import autoclass
                TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
                Locale = autoclass("java.util.Locale")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")

                tts = TextToSpeech(PythonActivity.mActivity, None)
                tts.setLanguage(Locale(self.target_lang))
                tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, "TTS_ID")
            except Exception as e:
                print(f"TTS Error: {e}")
        else:
            self._show_simple_popup("TTS", "ხმოვანი წაკითხვა მხარდაჭერილია მხოლოდ Android-ზე.")

    def clear_input_text(self):
        trigger_vibration()
        self.input_text.text = ""
        self.output_text.text = ""

    def copy_to_clipboard(self):
        trigger_vibration()
        text = self.output_text.text
        if text:
            Clipboard.copy(text)
            self._show_simple_popup("შეტყობინება", "ტექსტი დაკოპირდა!")

    def save_to_favorites(self):
        trigger_vibration()
        orig = self.input_text.text.strip()
        trans = self.output_text.text.strip()
        if orig and trans:
            if db.add_favorite(self.source_lang, self.target_lang, orig, trans):
                self._show_simple_popup("ფავორიტები", "წარმატებით დაემატა ფავორიტებში!")

    def open_interpreter_mode(self):
        trigger_vibration()
        layout = BoxLayout(orientation="vertical", padding=10, spacing=8)
        lbl = Label(text="თარჯიმნის რეჟიმი\nაირჩიეთ ენა სასაუბროდ", halign="center")
        if FONT_PATH: lbl.font_name = FONT_PATH

        btn_src_kwargs = {"text": f"ლაპარაკი ({self.btn_src.text})", "size_hint_y": None, "height": "50dp"}
        if FONT_PATH: btn_src_kwargs["font_name"] = FONT_PATH
        btn_src = Button(**btn_src_kwargs)
        btn_src.bind(on_release=lambda x: self.start_speech_to_text(self.source_lang))

        btn_tgt_kwargs = {"text": f"ლაპარაკი ({self.btn_tgt.text})", "size_hint_y": None, "height": "50dp"}
        if FONT_PATH: btn_tgt_kwargs["font_name"] = FONT_PATH
        btn_tgt = Button(**btn_tgt_kwargs)
        btn_tgt.bind(on_release=lambda x: self.start_speech_to_text(self.target_lang))

        layout.add_widget(lbl)
        layout.add_widget(btn_src)
        layout.add_widget(btn_tgt)

        FontPopup(title="თარჯიმნის რეჟიმი", content=layout, size_hint=(0.85, 0.5)).open()

    def open_dictionary_hub(self):
        trigger_vibration()
        favs = db.get_favorites()
        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=6, padding=5)
        box.bind(minimum_height=box.setter("height"))

        if not favs:
            lbl_kwargs = {"text": "ფავორიტების ლექსიკონი ცარიელია", "size_hint_y": None, "height": "40dp"}
            if FONT_PATH: lbl_kwargs["font_name"] = FONT_PATH
            box.add_widget(Label(**lbl_kwargs))
        else:
            for item in favs:
                lbl_kwargs = {"text": f"- {item[0]} = {item[1]}", "size_hint_y": None, "height": "35dp"}
                if FONT_PATH: lbl_kwargs["font_name"] = FONT_PATH
                box.add_widget(Label(**lbl_kwargs))

        scroll.add_widget(box)
        FontPopup(title="ლექსიკონი / ფავორიტები", content=scroll, size_hint=(0.85, 0.8)).open()

    def open_quiz_mode(self):
        trigger_vibration()
        favs = db.get_favorites()
        if not favs:
            self._show_simple_popup("ქვიზი", "ქვიზის დასაწყებად ჯერ დაამატეთ სიტყვები ფავორიტებში!")
            return

        import random
        question = random.choice(favs)
        orig, correct_trans = question[0], question[1]

        layout = BoxLayout(orientation="vertical", padding=10, spacing=8)
        lbl_kwargs = {"text": f"რას ნიშნავს: '{orig}'?", "size_hint_y": None, "height": "40dp"}
        if FONT_PATH: lbl_kwargs["font_name"] = FONT_PATH
        lbl_q = Label(**lbl_kwargs)

        input_ans_kwargs = {"hint_text": "ჩაწერთ თარგმანი...", "size_hint_y": None, "height": "40dp", "multiline": False}
        if FONT_PATH: input_ans_kwargs["font_name"] = FONT_PATH
        input_ans = TextInput(**input_ans_kwargs)

        btn_chk_kwargs = {"text": "შემოწმება", "size_hint_y": None, "height": "45dp"}
        if FONT_PATH: btn_chk_kwargs["font_name"] = FONT_PATH
        btn_check = Button(**btn_chk_kwargs)

        popup = FontPopup(title="სიტყვების ქვიზი", content=layout, size_hint=(0.85, 0.5))

        def check_answer(instance):
            if input_ans.text.strip().lower() == correct_trans.strip().lower():
                self._show_simple_popup("შედეგი", "სწორია! პასუხი მართებულია.")
            else:
                self._show_simple_popup("შედეგი", f"არასწორია! სწორი პასუხია: {correct_trans}")
            popup.dismiss()

        btn_check.bind(on_release=check_answer)
        layout.add_widget(lbl_q)
        layout.add_widget(input_ans)
        layout.add_widget(btn_check)
        popup.open()

    def open_file_translator(self):
        trigger_vibration()
        layout = BoxLayout(orientation="vertical", padding=10, spacing=8)
        inp_path_kwargs = {"hint_text": "შეიყვანეთ .txt ფაილის სრული გზა...", "size_hint_y": None, "height": "40dp", "multiline": False}
        if FONT_PATH: inp_path_kwargs["font_name"] = FONT_PATH
        input_path = TextInput(**inp_path_kwargs)

        btn_load_kwargs = {"text": "ფაილის წაკითხვა", "size_hint_y": None, "height": "45dp"}
        if FONT_PATH: btn_load_kwargs["font_name"] = FONT_PATH
        btn_load = Button(**btn_load_kwargs)

        popup = FontPopup(title="ფაილის თარჯიმანი", content=layout, size_hint=(0.85, 0.5))

        def read_and_translate(instance):
            path = input_path.text.strip()
            if os.path.exists(path) and path.endswith(".txt"):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.input_text.text = content
                    popup.dismiss()
                except Exception as e:
                    self._show_simple_popup("შეცდომა", f"ფაილის წაკითხვა ვერ მოხერხდა: {e}")
            else:
                self._show_simple_popup("შეცდომა", "ფაილი ვერ მოიძებნა ან არ არის .txt ფორმატის!")

        btn_load.bind(on_release=read_and_translate)
        layout.add_widget(input_path)
        layout.add_widget(btn_load)
        popup.open()

    def check_for_updates(self, silent=True):
        def _thread_check():
            try:
                req = urllib.request.Request(
                    UPDATE_CHECK_URL,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        latest_ver = data.get("latest_version", CURRENT_VERSION)
                        if latest_ver != CURRENT_VERSION:
                            Clock.schedule_once(
                                lambda dt: self._show_simple_popup(
                                    "განახლება",
                                    f"ხელმისაწვდომია ახალი ვერსია v{latest_ver}!"
                                )
                            )
            except Exception:
                pass

        threading.Thread(target=_thread_check, daemon=True).start()

    def _show_simple_popup(self, title, message):
        layout = BoxLayout(orientation="vertical", padding=10, spacing=8)
        lbl_kwargs = {"text": message, "halign": "center", "valign": "middle"}
        if FONT_PATH: lbl_kwargs["font_name"] = FONT_PATH
        lbl = Label(**lbl_kwargs)
        lbl.bind(size=lbl.setter("text_size"))

        btn_kwargs = {"text": "OK", "size_hint_y": None, "height": "40dp"}
        if FONT_PATH: btn_kwargs["font_name"] = FONT_PATH
        btn = Button(**btn_kwargs)

        popup = FontPopup(title=title, content=layout, size_hint=(0.8, 0.4))
        btn.bind(on_release=popup.dismiss)

        layout.add_widget(lbl)
        layout.add_widget(btn)
        popup.open()

# ---------------------------------------------------------
# 9. მთავარი აპლიკაცია & Android Global Event Listener
# ---------------------------------------------------------
class LingoLensApp(App):
    def build(self):
        request_android_permissions()
        self._bind_android_events()
        
        self.sm = ScreenManager()
        self.main_screen = MainScreen(name="main")
        self.sm.add_widget(self.main_screen)
        return self.sm

    def _bind_android_events(self):
        if platform == "android":
            try:
                from android.activity import bind
                bind(on_activity_result=self._on_activity_result)
            except Exception as e:
                print(f"Activity bind error: {e}")

    def _on_activity_result(self, request_code, result_code, data):
        # 1002: STT შედეგი
        if request_code == 1002 and result_code == -1 and data is not None:
            try:
                from jnius import autoclass
                RecognizerIntent = autoclass("android.speech.RecognizerIntent")
                results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                if results and results.size() > 0:
                    recognized_text = results.get(0)
                    Clock.schedule_once(
                        lambda dt: self._set_screen_input_text(recognized_text)
                    )
            except Exception as e:
                print(f"STT process error: {e}")

        # 1003: კამერის შედეგი
        elif request_code == 1003 and result_code == -1:
            if hasattr(self.main_screen, 'photo_path') and self.main_screen.photo_path:
                if os.path.exists(self.main_screen.photo_path):
                    Clock.schedule_once(
                        lambda dt: self.main_screen.process_image_with_gemini(self.main_screen.photo_path)
                    )

    def _set_screen_input_text(self, text):
        self.main_screen.input_text.text = text


if __name__ == "__main__":
    LingoLensApp().run()
