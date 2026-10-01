import json
import threading
import urllib.request
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.RECORD_AUDIO, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

try:
    from utils.tts_engine import speak
except ImportError:
    def speak(text, lang, path, callback):
        if callback:
            callback("TTS Engine not available")

SUPPORTED_LANGUAGES = {
    "Georgian (Qartuli)": "ka",
    "English": "en",
    "Russian (Russkiy)": "ru",
    "Spanish (Espanol)": "es",
    "German (Deutsch)": "de",
    "French (Francais)": "fr",
    "Italian (Italiano)": "it",
    "Turkish (Turkce)": "tr",
    "Chinese (Zhongwen)": "zh",
    "Japanese (Nihongo)": "ja",
    "Korean (Hangugeo)": "ko",
    "Arabic (Al-Arabiyya)": "ar",
    "Portuguese (Portugues)": "pt",
    "Hindi": "hi"
}

class DialogueSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from kivy.app import App
        app = App.get_running_app()
        if hasattr(app, "GEORGIAN_FONT_NAME"):
            self.font_name = app.GEORGIAN_FONT_NAME


class DialogueWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(10)
        self.spacing = dp(10)
        self.size_hint = (1, 1)

        from kivy.app import App
        self.app = App.get_running_app()
        self.font = getattr(self.app, "GEORGIAN_FONT_NAME", "Roboto")

        lang_names = list(SUPPORTED_LANGUAGES.keys())

        # --- Person A Section ---
        person_a_header = BoxLayout(orientation="horizontal", size_hint_y=0.08, spacing=dp(5))
        lbl_person_a = Label(text="Person A", font_name=self.font, size_hint_x=0.5, halign="left")
        lbl_person_a.bind(size=lbl_person_a.setter("text_size"))
        
        self.sp_lang_a = Spinner(text="English", values=lang_names, font_name=self.font, size_hint_x=0.5, option_cls=DialogueSpinnerOption)
        person_a_header.add_widget(lbl_person_a)
        person_a_header.add_widget(self.sp_lang_a)
        self.add_widget(person_a_header)

        self.inp_a = TextInput(hint_text="Type here or use Mic / Isauðret...", font_name=self.font, multiline=True, size_hint_y=0.22)
        self.add_widget(self.inp_a)

        self.out_a = TextInput(hint_text="Translation / Targmani...", font_name=self.font, readonly=True, multiline=True, size_hint_y=0.22)
        self.add_widget(self.out_a)

        btn_box_a = BoxLayout(orientation="horizontal", size_hint_y=0.08, spacing=dp(5))
        self.btn_speak_a = Button(text="Live Mic A", font_name=self.font, on_press=lambda x: self.start_live_mic('A'))
        self.btn_trans_a = Button(text="Translate A->B", font_name=self.font, on_press=lambda x: self.translate_a_to_b())
        btn_box_a.add_widget(self.btn_speak_a)
        btn_box_a.add_widget(self.btn_trans_a)
        self.add_widget(btn_box_a)

        # --- Person B Section ---
        person_b_header = BoxLayout(orientation="horizontal", size_hint_y=0.08, spacing=dp(5))
        lbl_person_b = Label(text="Person B", font_name=self.font, size_hint_x=0.5, halign="left")
        lbl_person_b.bind(size=lbl_person_b.setter("text_size"))

        self.sp_lang_b = Spinner(text="Georgian (Qartuli)", values=lang_names, font_name=self.font, size_hint_x=0.5, option_cls=DialogueSpinnerOption)
        person_b_header.add_widget(lbl_person_b)
        person_b_header.add_widget(self.sp_lang_b)
        self.add_widget(person_b_header)

        self.inp_b = TextInput(hint_text="Mikrofoni an tекsti / Type here...", font_name=self.font, multiline=True, size_hint_y=0.22)
        self.add_widget(self.inp_b)

        self.out_b = TextInput(hint_text="Targmani / Translation...", font_name=self.font, readonly=True, multiline=True, size_hint_y=0.22)
        self.add_widget(self.out_b)

        btn_box_b = BoxLayout(orientation="horizontal", size_hint_y=0.08, spacing=dp(5))
        self.btn_speak_b = Button(text="Live Mic B", font_name=self.font, on_press=lambda x: self.start_live_mic('B'))
        self.btn_trans_b = Button(text="Translate B->A", font_name=self.font, on_press=lambda x: self.translate_b_to_a())
        btn_box_b.add_widget(self.btn_speak_b)
        btn_box_b.add_widget(self.btn_trans_b)
        self.add_widget(btn_box_b)

    def start_live_mic(self, person):
        lang_name = self.sp_lang_a.text if person == 'A' else self.sp_lang_b.text
        lang_code = SUPPORTED_LANGUAGES.get(lang_name, "en")
        target_input = self.inp_a if person == 'A' else self.inp_b
        btn = self.btn_speak_a if person == 'A' else self.btn_speak_b

        btn.text = "Listening..."
        target_input.text = "ismineba realur droshi... (Listening...)"

        def worker():
            if platform == 'android':
                try:
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    Intent = autoclass('android.content.Intent')
                    RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                    
                    activity = PythonActivity.mActivity
                    intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                    intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)
                    intent.putExtra(RecognizerIntent.EXTRA_PROMPT, f"Speak in {lang_name}")
                    
                    # Android Native Speech Recognition Call
                    activity.startActivityForResult(intent, 3001 if person == 'A' else 3002)
                except Exception as e:
                    print("Live Mic Error:", e)
                    Clock.schedule_once(lambda dt: setattr(target_input, "text", "Mic Error / Shecdoma"))
            else:
                # Desktop Test Simulation
                import time
                time.sleep(1.5)
                simulated_text = "Hello real-time dialogue test" if person == 'A' else "gamarjoba realuri dialogis testi"
                Clock.schedule_once(lambda dt: setattr(target_input, "text", simulated_text))

            Clock.schedule_once(lambda dt: setattr(btn, "text", f"Live Mic {person}"))

        threading.Thread(target=worker, daemon=True).start()

    def perform_translation(self, text, src_lang_name, target_lang_name, callback):
        if not text.strip():
            return
        src_code = SUPPORTED_LANGUAGES.get(src_lang_name, "en")
        target_code = SUPPORTED_LANGUAGES.get(target_lang_name, "ka")

        def worker():
            try:
                url = "http://37.27.255.1:8000/translate"
                payload = json.dumps({
                    "text": text,
                    "source": src_code,
                    "target": target_code,
                    "prompt": f"Provide a precise, grammatically clean, natural real-time spoken translation from {src_lang_name} to {target_lang_name}: {text}"
                }).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=8) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    result_text = (
                        res_data.get("translated_text")
                        or res_data.get("result")
                        or str(res_data)
                    )
                    callback(result_text)
            except Exception as e:
                print("Live Dialogue Translation Error:", e)
                callback("Shecdomaa servertan / Connection error")

        threading.Thread(target=worker, daemon=True).start()

    def translate_a_to_b(self):
        text = self.inp_a.text.strip()
        if not text:
            return
        self.out_a.text = "mushavdeba..."
        def on_result(res):
            Clock.schedule_once(lambda dt: setattr(self.out_a, "text", res))
            if hasattr(self.app, "save_to_history"):
                self.app.save_to_history(text, res)
            # Avtomaturi xmovani gamotqma (TTS) realur droshi
            if hasattr(self.app, "safe_speak"):
                lang_code = SUPPORTED_LANGUAGES.get(self.sp_lang_b.text, "ka")
                self.app.safe_speak(res, lang_code)
        self.perform_translation(text, self.sp_lang_a.text, self.sp_lang_b.text, on_result)

    def translate_b_to_a(self):
        text = self.inp_b.text.strip()
        if not text:
            return
        self.out_b.text = "mushavdeba..."
        def on_result(res):
            Clock.schedule_once(lambda dt: setattr(self.out_b, "text", res))
            if hasattr(self.app, "save_to_history"):
                self.app.save_to_history(text, res)
            # Avtomaturi xmovani gamotqma (TTS) realur droshi
            if hasattr(self.app, "safe_speak"):
                lang_code = SUPPORTED_LANGUAGES.get(self.sp_lang_a.text, "en")
                self.app.safe_speak(res, lang_code)
        self.perform_translation(text, self.sp_lang_b.text, self.sp_lang_a.text, on_result)
