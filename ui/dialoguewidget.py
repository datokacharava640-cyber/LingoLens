# ==============================================================================
# ui/dialoguewidget.py - LingoLens Dialogue & Voice Component
# ==============================================================================

import os
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.core.text import LabelBase

FONT_PATH = "font.ttf"
if os.path.exists(FONT_PATH):
    GEORGIAN_FONT_NAME = "GeorgianFont"
else:
    GEORGIAN_FONT_NAME = "Roboto"

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
            self.user_input.text = ""
            # აქ შეგიძლიათ დააკავშიროთ თქვენს თარგმანის ან AI ფუნქციას

    def toggle_microphone(self, instance):
        self.chat_output.text += "\n[მიკროფონი]: მოსმენა აქტიურია (ივარჯიშეთ ხმოვანი ბრძანებებით)..."
