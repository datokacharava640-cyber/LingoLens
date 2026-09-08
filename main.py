import os
import json
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

# ---------------------------------------------------------
# 0. აპლიკაციისა და პროექტის მეტამონაცემები / ლიცენზია
# ---------------------------------------------------------
APP_NAME = "LingoLens"
CURRENT_VERSION = "1.0.0"
AUTHOR_NAME = "Dato Kacharava"
CREATION_DATE = "2026-09-08"
LICENSE_NAME = "EISI / MIT Open License"

UPDATE_CHECK_URL = "https://raw.githubusercontent.com/example/lingolens/main/version.json"

APP_CREDITS_TEXT = (
    f"{APP_NAME} v{CURRENT_VERSION} | შექმნის თარიღი: {CREATION_DATE}\n"
    f"ავტორი: {AUTHOR_NAME} | ლიცენზია: {LICENSE_NAME}\n"
    "Powered by Google Translate & Gemini APIs"
)

# ---------------------------------------------------------
# 1. ფონტის უსაფრთხო ჩატვირთვა
# ---------------------------------------------------------
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None

# ---------------------------------------------------------
# 2. მსოფლიოს ენების სრული/გაფართოებული სია
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
                Permission.RECORD_AUDIO,
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
# 4. ლოკალური მონაცემთა ბაზა (JSON Base)
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
# 5. FontPopup კომპონენტი
# ---------------------------------------------------------
class FontPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if FONT_PATH:
            self.title_font = FONT_PATH

# ---------------------------------------------------------
# 6. მთავარი ეკრანი (MainScreen)
# ---------------------------------------------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "auto"
        self.target_lang = "ka"
        self._debounce_event = None

        self._build_ui()
        if platform == "android":
            self._setup_android_stt_listener()

        # ავტომატური განახლების შემოწმება აპლიკაციის ჩართვისას
        Clock.schedule_once(lambda dt: self.check_for_updates(silent=True), 3)

    def _build_ui(self):
        main_layout = BoxLayout(orientation="vertical", padding=10, spacing=8)

        # ენების არჩევის ზოლი
        lang_layout = BoxLayout(size_hint_y=None, height="45dp", spacing=5)
        
        btn_src_kwargs = {"text": "ავტოდაჭერა", "size_hint_x": 0.4}
        if FONT_PATH: btn_src_kwargs["font_name"] = FONT_PATH
        self.btn_src = Button(**btn_src_kwargs)
        self.btn_src.bind(on_release=lambda x: self.open_language_selector("source"))

        btn_swap_kwargs = {"text": "⇄", "size_hint_x": 0.2}
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

        # შეყვანის ტექსტური არე
        inp_kwargs = {
            "hint_text": "ჩაწერეთ ან ჩასვით ტექსტი...",
            "size_hint_y": 0.25,
            "multiline": True,
            "font_size": "16sp"
        }
        if FONT_PATH: inp_kwargs["font_name"] = FONT_PATH
        self.input_text = TextInput(**inp_kwargs)
        self.input_text.bind(text=lambda instance, val: self.on_live_translate(val))

        # მართვის ღილაკები
        ctrl_layout = BoxLayout(size_hint_y=None, height="40dp", spacing=5)
        
        btn_stt_kwargs = {"text": "🎤 ხმა", "size_hint_x": 0.25}
        if FONT_PATH: btn_stt_kwargs["font_name"] = FONT_PATH
        btn_stt = Button(**btn_stt_kwargs)
        btn_stt.bind(on_release=lambda x: self.start_speech_to_text(self.source_lang))

        btn_clr_kwargs = {"text": "🗑️ გასუფთავება", "size_hint_x": 0.35}
        if FONT_PATH: btn_clr_kwargs["font_name"] = FONT_PATH
        btn_clr = Button(**btn_clr_kwargs)
        btn_clr.bind(on_release=lambda x: self.clear_input_text())

        btn_int_kwargs = {"text": "💬 თარჯიმანი", "size_hint_x": 0.4}
        if FONT_PATH: btn_int_kwargs["font_name"] = FONT_PATH
        btn_int = Button(**btn_int_kwargs)
        btn_int.bind(on_release=lambda x: self.open_interpreter_mode())

        ctrl_layout.add_widget(btn_stt)
        ctrl_layout.add_widget(btn_clr)
        ctrl_layout.add_widget(btn_int)

        # შედეგის არე
        out_kwargs = {
            "hint_text": "თარგმანი გამოჩნდება აქ...",
            "size_hint_y": 0.25,
            "multiline": True,
            "readonly": True,
            "font_size": "16sp"
        }
        if FONT_PATH: out_kwargs["font_name"] = FONT_PATH
        self.output_text = TextInput(**out_kwargs)

        # შედეგის მართვის ღილაკები
        out_ctrl = BoxLayout(size_hint_y=None, height="40dp", spacing=5)
        
        btn_tts_kwargs = {"text": "🔊 წაკითხვა"}
        if FONT_PATH: btn_tts_kwargs["font_name"] = FONT_PATH
        btn_tts = Button(**btn_tts_kwargs)
        btn_tts.bind(on_release=lambda x: self.speak_output_text())

        btn_copy_kwargs = {"text": "📋 კოპირება"}
        if FONT_PATH: btn_copy_kwargs["font_name"] = FONT_PATH
        btn_copy = Button(**btn_copy_kwargs)
        btn_copy.bind(on_release=lambda x: self.copy_to_clipboard())

        btn_fav_kwargs = {"text": "⭐ ფავორიტი"}
        if FONT_PATH: btn_fav_kwargs["font_name"] = FONT_PATH
        btn_fav = Button(**btn_fav_kwargs)
        btn_fav.bind(on_release=lambda x: self.save_to_favorites())

        out_ctrl.add_widget(btn_tts)
        out_ctrl.add_widget(btn_copy)
        out_ctrl.add_widget(btn_fav)

        # დამატებითი ფუნქციების ნავიგაცია
        nav_layout = BoxLayout(size_hint_y=None, height="40dp", spacing=5)
        
        btn_dict_kwargs = {"text": "📚 ლექსიკონი"}
        if FONT_PATH: btn_dict_kwargs["font_name"] = FONT_PATH
        btn_dict = Button(**btn_dict_kwargs)
        btn_dict.bind(on_release=lambda x: self.open_dictionary_hub())

        btn_quiz_kwargs = {"text": "🎮 ქვიზი"}
        if FONT_PATH: btn_quiz_kwargs["font_name"] = FONT_PATH
        btn_quiz = Button(**btn_quiz_kwargs)
        btn_quiz.bind(on_release=lambda x: self.open_quiz_mode())

        btn_file_kwargs = {"text": "📄 .TXT ფაილი"}
        if FONT_PATH: btn_file_kwargs["font_name"] = FONT_PATH
        btn_file = Button(**btn_file_kwargs)
        btn_file.bind(on_release=lambda x: self.open_file_translator())

        nav_layout.add_widget(btn_dict)
        nav_layout.add_widget(btn_quiz)
        nav_layout.add_widget(btn_file)

        # ავტორისა და ლიცენზიის ფუტერი
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
                                    "განახლება ხელმისაწვდომია",
                                    f"ხელმისაწვდომია ახალი ვერსია v{latest_ver}!\nგთხოვთ განახლოთ აპლიკაცია."
                                )
                            )
                        elif not silent:
                            Clock.schedule_once(
                                lambda dt: self._show_simple_popup(
                                    "განახლება", "თქვენ იყენებთ უახლეს ვერსიას."
                                )
                            )
            except Exception:
                if not silent:
                    Clock.schedule_once(
                        lambda dt: self._show_simple_popup(
                            "განახლება", "განახლების შემოწმება ვერ მოხერხდა."
                        )
                    )

        threading.Thread(target=_thread_check, daemon=True).start()

    def _setup_android_stt_listener(self):
        try:
            from android.activity import bind
            bind(on_activity_result=self._on_activity_result)
        except Exception as e:
            print(f"Activity bind error: {e}")

    def _on_activity_result(self, request_code, result_code, data):
        if request_code == 1002 and result_code == -1 and data is not None:
            try:
                from jnius import autoclass
                RecognizerIntent = autoclass("android.speech.RecognizerIntent")
                results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                if results and results.size() > 0:
                    recognized_text = results.get(0)
                    Clock.schedule_once(lambda dt: self._update_input_from_stt(recognized_text))
            except Exception as e:
                print(f"STT Process Error: {e}")

    def _update_input_from_stt(self, text):
        self.input_text.text = text

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
                self._show_simple_popup("STT ხარვეზი", "ხმოვანი შეყვანა მიუწვდომელია.")
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
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        raw_data = response.read().decode('utf-8')
                        data = json.loads(raw_data)
                        translated = "".join([item[0] for item in data[0] if item[0]])
                        Clock.schedule_once(
                            lambda dt: self._handle_translation_success(text, translated)
                        )
                    else:
                        Clock.schedule_once(
                            lambda dt: self._set_output_text("სერვერის ხარვეზი")
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
                lbl_kwargs = {"text": f"• {item[0]} = {item[1]}", "size_hint_y": None, "height": "35dp"}
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
                        self.input_text.text = f.read()[:1000]
                    popup.dismiss()
                except Exception:
                    self._show_simple_popup("შეცდომა", "ფაილის წაკითხვა ვერ მოხერხდა.")
            else:
                self._show_simple_popup("შეცდომა", "ფაილი ვერ მოიძებნა ან არ არის .txt ფორმატის.")

        btn_load.bind(on_release=read_and_translate)
        layout.add_widget(input_path)
        layout.add_widget(btn_load)
        popup.open()

    def _show_simple_popup(self, title_text, msg_text):
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        lbl_kwargs = {"text": msg_text, "halign": "center", "valign": "middle"}
        if FONT_PATH: lbl_kwargs["font_name"] = FONT_PATH
        lbl = Label(**lbl_kwargs)
        lbl.bind(size=lbl.setter("text_size"))

        btn_kwargs = {"text": "OK", "size_hint_y": None, "height": "40dp"}
        if FONT_PATH: btn_kwargs["font_name"] = FONT_PATH
        btn = Button(**btn_kwargs)

        popup = FontPopup(title=title_text, content=layout, size_hint=(0.8, 0.4))
        btn.bind(on_release=popup.dismiss)

        layout.add_widget(lbl)
        layout.add_widget(btn)
        popup.open()

# ---------------------------------------------------------
# 7. App Entry Point
# ---------------------------------------------------------
class LingoLensApp(App):
    def build(self):
        request_android_permissions()
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        return sm

if __name__ == "__main__":
    LingoLensApp().run()
