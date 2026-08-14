import threading
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import requests

# 10 მოდულის იმპორტი modules/ საქაღალდიდან
from modules.wake_word import handle_wake_word
from modules.walkie_talkie import handle_walkie_talkie
from modules.ar_camera import handle_ar_camera
from modules.slang_decoder import handle_slang
from modules.offline_mode import OfflineEngine
from modules.viral_share import generate_share_card
from modules.travel_sos import handle_travel_sos
from modules.coach_mode import evaluate_pronunciation
from modules.smartwatch import sync_wearable
from modules.doc_summarizer import summarize_doc

class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro"
        self.server_url = "https://YOUR-RENDER-APP.onrender.com/process_voice"
        self.offline_engine = OfflineEngine()

        root = BoxLayout(orientation='vertical', padding=12, spacing=8)

        # Header
        header = Label(
            text="[b]✨ LingoLens AI Ecosystem[/b]",
            markup=True,
            font_size='20sp',
            size_hint_y=0.08
        )
        root.add_widget(header)

        self.status_label = Label(
            text="🟢 System Ready. All 10 Modules Active.",
            font_size='13sp',
            size_hint_y=0.07,
            color=(0.2, 0.8, 0.2, 1)
        )
        root.add_widget(self.status_label)

        # Input Area
        self.input_field = TextInput(
            hint_text="Enter text or say 'LingoLens'...",
            multiline=True,
            size_hint_y=0.22
        )
        root.add_widget(self.input_field)

        # Output Display
        self.output_label = Label(
            text="[Module Output Will Appear Here]",
            markup=True,
            size_hint_y=0.23
        )
        root.add_widget(self.output_label)

        # Control Panel Grid
        scroll = ScrollView(size_hint_y=0.40)
        grid = GridLayout(cols=2, spacing=8, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        btn_specs = [
            ("🎙️ Wake Word System", self.feat_wake_word, (0.2, 0.6, 1, 1)),
            ("📻 Walkie-Talkie", self.feat_walkie_talkie, (0.3, 0.7, 0.9, 1)),
            ("👁️ AR Camera Translate", self.feat_ar_camera, (0.9, 0.4, 0.2, 1)),
            ("🧠 Slang Decoder", self.feat_slang_decoder, (0.8, 0.3, 0.8, 1)),
            ("📶 Offline Mode", self.feat_offline_mode, (0.5, 0.5, 0.5, 1)),
            ("📱 Viral Share Card", self.feat_viral_share, (0.9, 0.2, 0.5, 1)),
            ("🚨 Travel SOS & Price", self.feat_travel_sos, (0.9, 0.1, 0.1, 1)),
            ("🎯 Coach & Flashcards", self.feat_coach, (0.2, 0.8, 0.4, 1)),
            ("⌚ Smartwatch / Earbuds", self.feat_smartwatch, (0.4, 0.4, 0.8, 1)),
            ("📄 Doc Summarizer", self.feat_doc_summarizer, (0.6, 0.4, 0.2, 1))
        ]

        for text, callback, color in btn_specs:
            btn = Button(
                text=text,
                size_hint_y=None,
                height=50,
                background_color=color,
                font_size='12sp'
            )
            btn.bind(on_press=callback)
            grid.add_widget(btn)

        scroll.add_widget(grid)
        root.add_widget(scroll)

        # Background Wake Word Listener
        Clock.schedule_interval(self.check_wake_word, 2.0)

        return root

    def check_wake_word(self, dt):
        txt = self.input_field.text
        is_triggered, msg = handle_wake_word(txt)
        if is_triggered:
            self.status_label.text = msg
            self.input_field.text = ""
            self.output_label.text = "⚡ Wake Word Detected! How can LingoLens assist?"

    def feat_wake_word(self, instance):
        self.status_label.text = "🎙️ Listening for 'LingoLens'..."

    def feat_walkie_talkie(self, instance):
        txt = self.input_field.text.strip()
        res = handle_walkie_talkie(txt)
        self.output_label.text = res

    def feat_ar_camera(self, instance):
        res = handle_ar_camera()
        self.output_label.text = res

    def feat_slang_decoder(self, instance):
        txt = self.input_field.text.strip()
        res = handle_slang(txt)
        self.output_label.text = res

    def feat_offline_mode(self, instance):
        state = self.offline_engine.toggle()
        status = "ACTIVE" if state else "DISABLED"
        self.output_label.text = f"📶 Offline Mode: [b]{status}[/b]"

    def feat_viral_share(self, instance):
        txt = self.input_field.text.strip() or "LingoLens AI"
        res = generate_share_card(txt)
        self.output_label.text = res

    def feat_travel_sos(self, instance):
        res = handle_travel_sos(10)
        self.output_label.text = res

    def feat_coach(self, instance):
        res = evaluate_pronunciation()
        self.output_label.text = res

    def feat_smartwatch(self, instance):
        res = sync_wearable()
        self.output_label.text = res

    def feat_doc_summarizer(self, instance):
        txt = self.input_field.text.strip()
        res = summarize_doc(txt)
        self.output_label.text = res

if __name__ == '__main__':
    LingoLensApp().run()
