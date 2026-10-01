import os
import json
import threading
import urllib.request
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.app import App

try:
    from utils.tts_engine import speak
except ImportError:
    def speak(text, lang, path, callback):
        if callback:
            callback("TTS Engine not available")

class DialogueWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(10)
        self.spacing = dp(10)
        
        app = App.get_running_app()
        font = getattr(app, "GEORGIAN_FONT_NAME", "Roboto")

        # --- Person A Section ---
        self.add_widget(Label(text="Person A (English)", font_name=font, size_hint_y=0.05))
        self.inp_a = TextInput(hint_text="Type here / ისაუბრეთ...", font_name=font, size_hint_y=0.2, multiline=False)
        self.out_a = TextInput(hint_text="Translation / თარგმანი...", font_name=font, readonly=True, size_hint_y=0.2, multiline=False)
        
        btn_box_a = BoxLayout(orientation="horizontal", size_hint_y=0.1, spacing=dp(5))
        self.btn_speak_a = Button(text="Speak", font_name=font)
        self.btn_trans_a = Button(text="Translate", font_name=font)
        self.btn_speak_a.bind(on_press=lambda x: self.speak_text(self.out_a.text, "en"))
        self.btn_trans_a.bind(on_press=lambda x: self.translate_a_to_b())
        btn_box_a.add_widget(self.btn_speak_a)
        btn_box_a.add_widget(self.btn_trans_a)

        self.add_widget(self.inp_a)
        self.add_widget(self.out_a)
        self.add_widget(btn_box_a)

        # --- Person B Section ---
        self.add_widget(Label(text="Person B (Georgian)", font_name=font, size_hint_y=0.05))
        self.inp_b = TextInput(hint_text="მიკროფონი... / Type here...", font_name=font, size_hint_y=0.2, multiline=False)
        self.out_b = TextInput(hint_text="თარგმანი / Translation...", font_name=font, readonly=True, size_hint_y=0.2, multiline=False)
        
        btn_box_b = BoxLayout(orientation="horizontal", size_hint_y=0.1, spacing=dp(5))
        self.btn_speak_b = Button(text="საუბარი", font_name=font)
        self.btn_trans_b = Button(text="Translate", font_name=font)
        self.btn_speak_b.bind(on_press=lambda x: self.speak_text(self.out_b.text, "ka"))
        self.btn_trans_b.bind(on_press=lambda x: self.translate_b_to_a())
        btn_box_b.add_widget(self.btn_speak_b)
        btn_box_b.add_widget(self.btn_trans_b)

        self.add_widget(self.inp_b)
        self.add_widget(self.out_b)
        self.add_widget(btn_box_b)

    def translate_text_request(self, text, src, target, callback):
        def worker():
            try:
                url = "http://37.27.255.1:8000/translate"
                payload = json.dumps({
                    "text": text,
                    "source": src,
                    "target": target,
                    "prompt": f"Translate accurately from {src} to {target}: {text}"
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
                print("Dialogue Translation Error:", e)
                callback("შეცდომაა სერვერთან")

        threading.Thread(target=worker, daemon=True).start()

    def translate_a_to_b(self):
        text = self.inp_a.text.strip()
        if not text:
            return
        self.out_a.text = "მუშავდება..."
        def on_result(res):
            Clock.schedule_once(lambda dt: setattr(self.out_a, "text", res))
        self.translate_text_request(text, "en", "ka", on_result)

    def translate_b_to_a(self):
        text = self.inp_b.text.strip()
        if not text:
            return
        self.out_b.text = "მუშავდება..."
        def on_result(res):
            Clock.schedule_once(lambda dt: setattr(self.out_b, "text", res))
        self.translate_text_request(text, "ka", "en", on_result)

    def speak_text(self, text, lang):
        if not text or text == "მუშავდება..." or text.startswith("შეცდომა"):
            return
        app = App.get_running_app()
        data_dir = app.user_data_dir if app else "."
        try:
            speak(text, lang, data_dir, lambda msg: print(msg))
        except Exception as e:
            print("TTS error:", e)
