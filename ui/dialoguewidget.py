# ==============================================================================
# ui/dialoguewidget.py - LingoLens Dialogue & Voice Component
# ==============================================================================

import os
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.utils import platform

FONT_PATH = "font.ttf"
if os.path.exists(FONT_PATH):
    GEORGIAN_FONT_NAME = "GeorgianFont"
else:
    GEORGIAN_FONT_NAME = "Roboto"

try:
    from utils.translator import translate_text
except ImportError:
    import threading
    import urllib.request
    import json

    def translate_text(prompt, text, src_lang, target_lang, callback):
        def worker():
            try:
                url = "http://37.27.255.1:8000/translate"
                payload = json.dumps({
                    "text": text,
                    "source": src_lang,
                    "target": target_lang,
                    "prompt": prompt
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
                print("Server connection error:", e)
                callback(None)
        threading.Thread(target=worker, daemon=True).start()


class DialogueWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(15)
        self.spacing = dp(10)
        self.size_hint = (1, 1)

        font = GEORGIAN_FONT_NAME

        # სათაური
        self.add_widget(Label(
            text="🎙️ რეალურ დროში დიალოგი / ხმოვანი თარგმანი",
            font_name=font,
            size_hint_y=0.1
        ))

        # ჩატის / საუბრის ისტორიის ველები
        self.chat_output = TextInput(
            text="სისტემა მზად არის დიალოგისთვის...\n",
            font_name=font,
            readonly=True,
            multiline=True,
            size_hint_y=0.6
        )
        self.add_widget(self.chat_output)

        # მომხმარებლის შეყვანის ველი
        self.user_input = TextInput(
            hint_text="ჩაწერეთ ან თქვით რამე...",
            font_name=font,
            multiline=False,
            size_hint_y=0.15
        )
        self.add_widget(self.user_input)

        # მართვის ღილაკები
        btn_layout = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=0.15)
        
        self.btn_send = Button(
            text="გაგზავნა",
            font_name=font,
            background_color=(0.1, 0.6, 0.8, 1)
        )
        self.btn_send.bind(on_press=self.send_dialogue_message)

        self.btn_mic = Button(
            text="🎙️ მიკროფონი",
            font_name=font,
            background_color=(0.8, 0.3, 0.2, 1)
        )
        self.btn_mic.bind(on_press=self.toggle_microphone)

        btn_layout.add_widget(self.btn_send)
        btn_layout.add_widget(self.btn_mic)
        self.add_widget(btn_layout)

    def send_dialogue_message(self, instance):
        text = self.user_input.text.strip()
        if text:
            self.chat_output.text += f"\nმომხმარებელი: {text}"
            user_text = text
            self.user_input.text = ""
            
            # სერვერთან ან AI-სთან დაკავშირება დიალოგის რეჟიმში
            def on_res(res):
                answer = res if res else "ვერ მოხერხდა პასუხის მიღება."
                Clock.schedule_once(lambda dt: setattr(
                    self.chat_output, 
                    'text', 
                    self.chat_output.text + f"\nLingoLens AI: {answer}\n"
                ))

            try:
                translate_text(
                    prompt=f"Continue dialogue and reply naturally in Georgian: {user_text}",
                    text=user_text,
                    src_lang="ka",
                    target_lang="ka",
                    callback=on_res
                )
            except Exception as e:
                print("Dialogue transmission error:", e)

    def toggle_microphone(self, instance):
        self.chat_output.text += "\n[მიკროფონი]: მოსმენა აქტიურია (ივარჯიშეთ ხმოვანი ბრძანებებით)..."
        # აქ შეგიძლიათ დაამატოთ ხმის ჩაწერის და Android Speech API-ს გამოძახების ლოგიკა,
        # რადგან მიკროფონის ნებართვა მთავარ ფაილში (main.py) უკვე მოთხოვნილია.
