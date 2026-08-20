import sys
import traceback
import os
import sqlite3
import urllib.request
import threading
import ssl
from urllib.parse import quote

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.utils import platform
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.network.urlrequest import UrlRequest

# ---------------------------------------------------------
# 0. FONT REGISTRATION
# ---------------------------------------------------------
try:
    LabelBase.register(name='GeorgianFont', fn_regular='font.ttf')
    DEFAULT_FONT = 'GeorgianFont'
except Exception:
    DEFAULT_FONT = 'Roboto'

class CustomSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = DEFAULT_FONT

LANGUAGES = {
    "English": {"code": "en", "stt": "en-US"},
    "ქართული": {"code": "ka", "stt": "ka-GE"},
    "რუსული (Russian)": {"code": "ru", "stt": "ru-RU"},
    "თურქული (Turkish)": {"code": "tr", "stt": "tr-TR"},
    "ესპანური (Spanish)": {"code": "es", "stt": "es-ES"},
    "ფრანგული (French)": {"code": "fr", "stt": "fr-FR"},
    "გერმანული (German)": {"code": "de", "stt": "de-DE"},
    "იტალიური (Italian)": {"code": "it", "stt": "it-IT"},
    "არაბული (Arabic)": {"code": "ar", "stt": "ar-SA"}
}

# ---------------------------------------------------------
# 1. DATABASE MANAGER
# ---------------------------------------------------------
class SafeDatabase:
    def __init__(self, user_data_dir="."):
        self.enabled = False
        self.db_path = ":memory:"
        try:
            if platform == 'android':
                self.db_path = os.path.join(user_data_dir, "lingolens.db")
            else:
                self.db_path = "lingolens.db"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, source_text TEXT, translated_text TEXT)")
            self.enabled = True
        except Exception as e:
            print(f"DB Disabled: {e}")

    def add(self, src, trans):
        if not self.enabled: return
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT INTO history (source_text, translated_text) VALUES (?, ?)", (src, trans))
        except Exception:
            pass

    def get(self):
        if not self.enabled: return []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT source_text, translated_text FROM history ORDER BY id DESC LIMIT 30")
                return cursor.fetchall()
        except Exception:
            return []

    def clear(self):
        if not self.enabled: return
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM history")
        except Exception:
            pass

# ---------------------------------------------------------
# 2. MAIN UI
# ---------------------------------------------------------
class LingoLensUI(BoxLayout):
    def __init__(self, user_data_dir=".", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
        self.user_data_dir = user_data_dir
        self.db = SafeDatabase(user_data_dir)
        self.media_player = None
        self.active_src_lang = "en"
        self.active_target_lang = "ka"

        if platform == 'android':
            from android.activity import bind
            bind(on_activity_result=self.on_activity_result)

        # 1. Header
        header = BoxLayout(size_hint_y=0.08, spacing=5)
        title = Label(text="LingoLens Ultra Pro", font_size='18sp', bold=True, font_name=DEFAULT_FONT)
        btn_menu = Button(text="[=] მენიუ", size_hint_x=0.3, font_name=DEFAULT_FONT)
        btn_menu.bind(on_press=self.open_menu)
        header.add_widget(title)
        header.add_widget(btn_menu)
        self.add_widget(header)

        # 2. Foreigner Selection Dropdown
        foreign_box = BoxLayout(size_hint_y=0.08, spacing=5)
        lbl_foreign = Label(text="უცხოელის ენა:", font_name=DEFAULT_FONT, size_hint_x=0.4)
        
        foreign_options = [k for k in LANGUAGES.keys() if k != "ქართული"]
        self.foreign_spinner = Spinner(
            text="English", 
            values=foreign_options, 
            size_hint_x=0.6, 
            font_name=DEFAULT_FONT,
            option_cls=CustomSpinnerOption
        )
        foreign_box.add_widget(lbl_foreign)
        foreign_box.add_widget(self.foreign_spinner)
        self.add_widget(foreign_box)

        # 3. Text Area Display
        input_container = BoxLayout(size_hint_y=0.3, spacing=5)
        self.input_text = TextInput(
            hint_text="მოსმენილი ტექსტი...", 
            font_name=DEFAULT_FONT,
            size_hint_x=0.8
        )
        btn_speak = Button(
            text="🔊\nხმა", 
            size_hint_x=0.2, 
            font_name=DEFAULT_FONT, 
            font_size='13sp',
            halign='center'
        )
        btn_speak.bind(on_press=self.speak_text)

        input_container.add_widget(self.input_text)
        input_container.add_widget(btn_speak)
        self.add_widget(input_container)

        # 4. Output Area
        self.output_label = Label(
            text="ნათარგმნი ტექსტი...", 
            font_size='15sp', 
            font_name=DEFAULT_FONT, 
            size_hint_y=0.2,
            halign='left',
            valign='top'
        )
        self.output_label.bind(size=self.output_label.setter('text_size'))
        self.add_widget(self.output_label)

        # 5. Dual Conversation Buttons
        voice_box = BoxLayout(size_hint_y=0.2, spacing=8)
        
        btn_foreigner = Button(
            text="🎤 უცხოელი საუბრობს", 
            font_name=DEFAULT_FONT,
            halign='center',
            background_color=(0.2, 0.6, 0.8, 1)
        )
        btn_foreigner.bind(on_press=self.listen_foreigner)

        btn_georgian = Button(
            text="🎤 მე ვსაუბრობ (ქართულად)", 
            font_name=DEFAULT_FONT,
            halign='center',
            background_color=(0.2, 0.8, 0.4, 1)
        )
        btn_georgian.bind(on_press=self.listen_georgian)

        voice_box.add_widget(btn_foreigner)
        voice_box.add_widget(btn_georgian)
        self.add_widget(voice_box)

    def on_activity_result(self, request_code, result_code, intent):
        if request_code == 1001 and result_code == -1:
            try:
                from jnius import autoclass
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                results = intent.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                if results and results.size() > 0:
                    text = results.get(0)
                    Clock.schedule_once(lambda dt: self.process_voice(text), 0.1)
            except Exception as e:
                print(f"STT Error: {e}")

    def process_voice(self, text):
        self.input_text.text = text
        self.translate_and_speak(text)

    # უცხოელი საუბრობს (მაგ: English -> ქართული)
    def listen_foreigner(self, instance):
        selected_name = self.foreign_spinner.text
        lang_data = LANGUAGES.get(selected_name, LANGUAGES["English"])
        
        self.active_src_lang = lang_data["code"]
        self.active_target_lang = "ka"
        
        self.start_stt(lang_data["stt"])

    # მე ვსაუბრობ (ქართული -> უცხოელის ენა)
    def listen_georgian(self, instance):
        selected_name = self.foreign_spinner.text
        lang_data = LANGUAGES.get(selected_name, LANGUAGES["English"])
        
        self.active_src_lang = "ka"
        self.active_target_lang = lang_data["code"]
        
        self.start_stt("ka-GE")

    def start_stt(self, stt_code):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')

                intent = Intent(RecognizerIntent.ACTION_WEB_SEARCH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, stt_code)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, stt_code)
                intent.putExtra(RecognizerIntent.EXTRA_ONLY_RETURN_LANGUAGE_PREFERENCE, stt_code)

                currentActivity = PythonActivity.mActivity
                currentActivity.startActivityForResult(intent, 1001)
            except Exception as e:
                self.show_info(f"ხმის შეცდომა: {e}")
        else:
            self.show_info("მუშაობს მხოლოდ Android-ზე")

    def translate_and_speak(self, text):
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={self.active_src_lang}&tl={self.active_target_lang}&dt=t&q={quote(text)}"
        UrlRequest(url, on_success=self.on_trans_success, on_error=self.on_err, timeout=5)

    def on_trans_success(self, req, result):
        try:
            res = "".join([item[0] for item in result[0] if item[0]])
            self.output_label.text = res
            self.db.add(self.input_text.text[:30], res)
            self.speak_text(None)
        except Exception:
            self.output_label.text = "Parse Error"

    def on_err(self, req, error):
        self.output_label.text = "Network Error"

    def speak_georgian_azure(self, text):
        def download_and_play():
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                azure_key = "6nmGCEBuy5wT3XnOvxwDmAyt9RTJf3oWt1v3I7AgsdbY6fhUQRI5JQQJ99CHACYeBjFXJ3w3AAAYACOGWGgT"
                region = "eastus"
                url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"

                ssml = f"""<speak version='1.0' xml:lang='ka-GE'>
                    <voice xml:lang='ka-GE' name='ka-GE-EkaNeural'>{text}</voice>
                </speak>"""

                headers = {
                    'Ocp-Apim-Subscription-Key': azure_key,
                    'Content-Type': 'application/ssml+xml',
                    'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
                    'User-Agent': 'LingoLens'
                }

                req = urllib.request.Request(url, data=ssml.encode('utf-8'), headers=headers, method='POST')
                audio_path = os.path.join(self.user_data_dir, "ka_temp.mp3")

                with urllib.request.urlopen(req, context=ctx) as response, open(audio_path, 'wb') as f:
                    f.write(response.read())

                if platform == 'android':
                    from jnius import autoclass
                    MediaPlayer = autoclass('android.media.MediaPlayer')
                    if hasattr(self, 'media_player') and self.media_player:
                        try:
                            self.media_player.stop()
                            self.media_player.release()
                        except Exception:
                            pass
                    self.media_player = MediaPlayer()
                    self.media_player.setDataSource(audio_path)
                    self.media_player.prepare()
                    self.media_player.start()
            except Exception as e:
                print(f"Azure Georgian TTS Error: {e}")

        threading.Thread(target=download_and_play, daemon=True).start()

    def speak_text(self, instance):
        text = self.output_label.text.strip()
        if not text or text in ["ნათარგმნი ტექსტი...", "Parse Error", "Network Error"]:
            return

        if self.active_target_lang == "ka":
            self.speak_georgian_azure(text)
            return

        if platform == 'android':
            try:
                from jnius import autoclass
                MediaPlayer = autoclass('android.media.MediaPlayer')
                
                if hasattr(self, 'media_player') and self.media_player:
                    try:
                        self.media_player.stop()
                        self.media_player.release()
                    except Exception:
                        pass
                
                self.media_player = MediaPlayer()
                tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={quote(text)}&tl={self.active_target_lang}&client=tw-ob"
                self.media_player.setDataSource(tts_url)
                self.media_player.prepare()
                self.media_player.start()
            except Exception as e:
                print(f"Android Stream Audio Error: {e}")

    def open_menu(self, instance):
        p = Popup(title="მენიუ", size_hint=(0.8, 0.5), title_font=DEFAULT_FONT)
        box = BoxLayout(orientation='vertical', spacing=10, padding=10)

        btn_hist = Button(text="[H] ისტორია", font_name=DEFAULT_FONT)
        btn_hist.bind(on_press=lambda x: [p.dismiss(), self.open_history()])

        btn_clear = Button(text="[D] ისტორიის წაშლა", font_name=DEFAULT_FONT)
        btn_clear.bind(on_press=lambda x: [self.db.clear(), p.dismiss(), self.show_info("ისტორია წაიშალა")])

        btn_about = Button(text="[i] შესახებ", font_name=DEFAULT_FONT)
        btn_about.bind(on_press=lambda x: [p.dismiss(), self.open_about()])

        btn_close = Button(text="[X] დახურვა", font_name=DEFAULT_FONT)
        btn_close.bind(on_press=p.dismiss)

        box.add_widget(btn_hist)
        box.add_widget(btn_clear)
        box.add_widget(btn_about)
        box.add_widget(btn_close)

        p.content = box
        p.open()

    def open_history(self):
        p = Popup(title="თარგმანების ისტორია", size_hint=(0.85, 0.8), title_font=DEFAULT_FONT)
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=10)
        box.bind(minimum_height=box.setter('height'))

        items = self.db.get()
        if not items:
            box.add_widget(Label(text="ისტორია ცარიელია", font_name=DEFAULT_FONT, size_hint_y=None, height=40))
        else:
            for s, t in items:
                lbl = Label(text=f"• {s} -> {t}", font_name=DEFAULT_FONT, size_hint_y=None, height=40, halign='left', valign='middle')
                lbl.bind(size=lbl.setter('text_size'))
                box.add_widget(lbl)

        scroll.add_widget(box)
        p.content = scroll
        p.open()

    def open_about(self):
        p = Popup(title="შესახებ", size_hint=(0.8, 0.4), title_font=DEFAULT_FONT)
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text="LingoLens Ultra Pro v1.0\nორმხრივი დიალოგის მთარგმნელი", font_name=DEFAULT_FONT, halign='center')
        btn = Button(text="OK", font_name=DEFAULT_FONT, size_hint_y=0.4)
        btn.bind(on_press=p.dismiss)
        box.add_widget(lbl)
        box.add_widget(btn)
        p.content = box
        p.open()

    def show_info(self, text):
        p = Popup(title="შეტყობინება", size_hint=(0.7, 0.3), title_font=DEFAULT_FONT)
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=text, font_name=DEFAULT_FONT)
        btn = Button(text="OK", font_name=DEFAULT_FONT, size_hint_y=0.4)
        btn.bind(on_press=p.dismiss)
        box.add_widget(lbl)
        box.add_widget(btn)
        p.content = box
        p.open()

# ---------------------------------------------------------
# 3. APP LAUNCHER
# ---------------------------------------------------------
class LingoLensApp(App):
    def build(self):
        try:
            return LingoLensUI(user_data_dir=self.user_data_dir)
        except Exception:
            err = traceback.format_exc()
            return Label(text=f"Runtime Error:\n{err}", color=(1, 0, 0, 1), font_size='12sp', font_name=DEFAULT_FONT)

if __name__ == "__main__":
    LingoLensApp().run()
