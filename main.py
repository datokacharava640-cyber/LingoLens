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

class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro"
        self.server_url = "https://YOUR-RENDER-APP.onrender.com/process_voice"
        self.offline_mode = False

        # მთავარი კონტეინერი
        root = BoxLayout(orientation='vertical', padding=12, spacing=8)

        # 1. Header & Status Bar
        header = Label(
            text="[b]✨ LingoLens AI Ecosystem[/b]",
            markup=True,
            font_size='20sp',
            size_hint_y=0.08
        )
        root.add_widget(header)

        self.status_label = Label(
            text="🟢 System Ready. Say 'LingoLens' or choose a feature.",
            font_size='13sp',
            size_hint_y=0.07,
            color=(0.2, 0.8, 0.2, 1)
        )
        root.add_widget(self.status_label)

        # 2. Text Input Area
        self.input_field = TextInput(
            hint_text="Enter text, phrase, or wake word 'LingoLens'...",
            multiline=True,
            size_hint_y=0.22
        )
        root.add_widget(self.input_field)

        # 3. Output Display Area
        self.output_label = Label(
            text="[AI Result & Translation will appear here]",
            markup=True,
            size_hint_y=0.23
        )
        root.add_widget(self.output_label)

        # 4. Scrollable Feature Control Panel (10 Gold Features)
        scroll = ScrollView(size_hint_y=0.40)
        grid = GridLayout(cols=2, spacing=8, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        # --- 10 სუპერ ფუნქციის ღილაკები ---
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

        # Background Wake Word Listener (Every 2 seconds)
        Clock.schedule_interval(self.check_wake_word, 2.0)

        return root

    # ==========================================
    # 🎙️ BACKGROUND WAKE WORD CHECK
    # ==========================================
    def check_wake_word(self, dt):
        txt = self.input_field.text.lower()
        if "lingolens" in txt:
            self.status_label.text = "⚡ Wake Word Detected!"
            self.input_field.text = ""
            self.send_api_request("LingoLens Wake Word Triggered", "translate")

    # ==========================================
    # 🛠️ 10 FEATURE HANDLERS (FUNCTIONS)
    # ==========================================

    # 1. Wake Word Manual Trigger
    def feat_wake_word(self, instance):
        self.status_label.text = "🎙️ Listening for 'LingoLens'..."
        self.output_label.text = "Say [b]'LingoLens'[/b] into input or microphone."

    # 2. Walkie-Talkie Mode
    def feat_walkie_talkie(self, instance):
        txt = self.input_field.text.strip() or "Hello, nice to meet you!"
        self.send_api_request(txt, "translate")

    # 3. AR Camera Translation
    def feat_ar_camera(self, instance):
        self.status_label.text = "👁️ AR Camera Mode Requested"
        self.output_label.text = "📷 [AR Viewfinder]: Scanning text in real-time..."

    # 4. Slang & Cultural Decoder
    def feat_slang_decoder(self, instance):
        txt = self.input_field.text.strip() or "Break a leg"
        self.send_api_request(txt, "slang")

    # 5. Offline Mode Toggle
    def feat_offline_mode(self, instance):
        self.offline_mode = not self.offline_mode
        state = "ENABLED" if self.offline_mode else "DISABLED"
        self.status_label.text = f"📶 Offline Pack: {state}"
        self.output_label.text = f"Offline Mode is now [b]{state}[/b]."

    # 6. Viral Share Card Generator
    def feat_viral_share(self, instance):
        txt = self.input_field.text.strip() or "LingoLens AI"
        self.output_label.text = f"🎨 Generated Social Card for: [b]'{txt}'[/b]\nReady to share on TikTok/Reels!"

    # 7. Travel SOS & Currency Converter
    def feat_travel_sos(self, instance):
        self.status_label.text = "🚨 Travel SOS Activated"
        self.output_label.text = "🚨 [SOS]: 'I need assistance!'\n💰 [Converter]: $10 USD = 27.00 GEL"

    # 8. Pronunciation Coach & Flashcards
    def feat_coach(self, instance):
        txt = self.input_field.text.strip() or "Bonjour"
        self.send_api_request(txt, "coach")

    # 9. Smartwatch & Earbuds Sync
    def feat_smartwatch(self, instance):
        self.status_label.text = "⌚ Smartwatch / Earbuds Connected"
        self.output_label.text = "🎧 Bluetooth Audio Channel Active. Ready for voice commands."

    # 10. Document & Voice Summarizer
    def feat_doc_summarizer(self, instance):
        self.status_label.text = "📄 Document Summarizer Active"
        self.output_label.text = "📝 Select PDF/Document or record meeting note to summarize."

    # ==========================================
    # 🌐 BACKEND NETWORK CONTROLLER
    # ==========================================
    def send_api_request(self, text, mode):
        self.status_label.text = f"⏳ Processing request ({mode})..."
        threading.Thread(target=self._async_request, args=(text, mode), daemon=True).start()

    def _async_request(self, text, mode):
        try:
            payload = {"text": text, "mode": mode, "target_lang": "en"}
            res = requests.post(self.server_url, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                out = data.get('result_text', 'No response')
                Clock.schedule_once(lambda dt: self._update_ui(out, "✅ Success"), 0)
            else:
                Clock.schedule_once(lambda dt: self._update_ui(f"Error {res.status_code}", "❌ Server Error"), 0)
        except Exception:
            # Fallback mock for UI test
            Clock.schedule_once(lambda dt: self._update_ui(f"[{mode.upper()} Result]: {text}", "✅ Ready (Local Response)"), 0)

    def _update_ui(self, output_text, status_text):
        self.output_label.text = output_text
        self.status_label.text = status_text

if __name__ == '__main__':
    LingoLensApp().run()
