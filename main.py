import threading
import json
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.utils import platform
import requests

# --- მოდულების იმპორტი ---
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

from modules.floating_bubble import FloatingBubbleService
from modules.streak_system import StreakTracker
from modules.referral_system import ReferralEngine
from modules.voice_clone import VoiceCloner
from modules.live_interpreter import LiveInterpreterEngine
from modules.design_and_tools import LingoLensProUX
from modules.smart_features import SmartAppEngine

# Android-ის სისტემური ფონტის პოვნა, რომელსაც ქართული ენის სრული მხარდაჭერა აქვს
SYSTEM_FONT = "/system/fonts/NotoSansGeorgian-Regular.ttf"
if not os.path.exists(SYSTEM_FONT):
    SYSTEM_FONT = "/system/fonts/Roboto-Regular.ttf"

class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro"
        self.server_url = "https://YOUR-RENDER-APP.onrender.com/process_voice"

        self.offline_engine = OfflineEngine()
        self.bubble_svc = FloatingBubbleService()
        self.streak_tracker = StreakTracker()
        self.referral_engine = ReferralEngine()
        self.voice_cloner = VoiceCloner()
        self.live_interpreter = LiveInterpreterEngine()
        self.ux_engine = LingoLensProUX()
        self.smart_engine = SmartAppEngine()

        root = BoxLayout(orientation='vertical', padding=12, spacing=8)

        # 1. Header
        header = Label(
            text="[b]LingoLens Live AI Ecosystem[/b]",
            markup=True,
            font_size='22sp',
            font_name=SYSTEM_FONT,
            size_hint_y=0.08
        )
        root.add_widget(header)

        # 2. Status Bar
        self.status_label = Label(
            text=f"Engine Ready! | {self.streak_tracker.get_status()}",
            font_size='12sp',
            font_name=SYSTEM_FONT,
            size_hint_y=0.07,
            color=(0.2, 0.8, 0.2, 1)
        )
        root.add_widget(self.status_label)

        # 3. Text Input Area (სისტემური ფონტით ქართულისთვის)
        self.input_field = TextInput(
            hint_text="Enter text or Georgian words...",
            font_name=SYSTEM_FONT,
            font_size='16sp',
            multiline=True,
            size_hint_y=0.20
        )
        root.add_widget(self.input_field)

        # 4. Output Display Area
        self.output_label = Label(
            text="[AI Translation Output Will Appear Here]",
            markup=True,
            font_name=SYSTEM_FONT,
            size_hint_y=0.25
        )
        root.add_widget(self.output_label)

        # 5. Control Panel
        scroll = ScrollView(size_hint_y=0.40)
        grid = GridLayout(cols=2, spacing=8, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        btn_specs = [
            ("Hands-Free Live", self.feat_live_handsfree, (0.1, 0.7, 0.4, 1)),
            ("Floating Bubble", self.feat_toggle_bubble, (0.2, 0.6, 1, 1)),
            ("AI Voice Clone", self.feat_voice_clone, (0.9, 0.3, 0.5, 1)),
            ("Daily Streaks", self.feat_check_streak, (0.9, 0.5, 0.1, 1)),
            ("Invite & Rewards", self.feat_referral, (0.2, 0.8, 0.4, 1)),
            ("AR Camera View", self.feat_ar_camera, (0.9, 0.4, 0.2, 1)),
            ("Slang Decoder", self.feat_slang_decoder, (0.8, 0.3, 0.8, 1)),
            ("Offline Mode", self.feat_offline_mode, (0.5, 0.5, 0.5, 1)),
            ("Travel SOS & Rate", self.feat_travel_sos, (0.9, 0.1, 0.1, 1)),
            ("Doc Summarizer", self.feat_doc_summarizer, (0.6, 0.4, 0.2, 1))
        ]

        for text, callback, color in btn_specs:
            btn = Button(
                text=text,
                size_hint_y=None,
                height=50,
                background_color=color,
                font_size='12sp',
                font_name=SYSTEM_FONT
            )
            btn.bind(on_press=callback)
            grid.add_widget(btn)

        scroll.add_widget(grid)
        root.add_widget(scroll)

        Clock.schedule_once(self.ping_server, 0.5)
        Clock.schedule_interval(self.check_wake_word, 2.0)

        return root

    def on_start(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA,
                    Permission.RECORD_AUDIO,
                    Permission.INTERNET,
                    Permission.MODIFY_AUDIO_SETTINGS
                ])
            except Exception as e:
                print(f"Permissions Error: {e}")

    def ping_server(self, dt):
        def _ping():
            try:
                requests.post(self.server_url, json={"text": "ping", "mode": "ping"}, timeout=4)
                Clock.schedule_once(lambda d: setattr(self.status_label, 'text', f"Engine Ready! | {self.streak_tracker.get_status()}"), 0)
            except Exception:
                Clock.schedule_once(lambda d: setattr(self.status_label, 'text', f"Standby Mode | {self.streak_tracker.get_status()}"), 0)
        threading.Thread(target=_ping, daemon=True).start()

    def check_wake_word(self, dt):
        txt = self.input_field.text
        is_triggered, msg = handle_wake_word(txt)
        if is_triggered:
            self.status_label.text = msg
            self.input_field.text = ""
            self.output_label.text = "Wake Word Detected!"

    def feat_live_handsfree(self, instance):
        res = self.live_interpreter.toggle_handsfree_live()
        self.output_label.text = res

    def feat_toggle_bubble(self, instance):
        res = self.bubble_svc.toggle_bubble()
        self.output_label.text = res

    def feat_voice_clone(self, instance):
        txt = self.input_field.text.strip() or "Hello, this is my AI cloned voice."
        res = self.voice_cloner.translate_in_custom_voice(txt)
        self.output_label.text = res

    def feat_check_streak(self, instance):
        res = self.streak_tracker.record_activity()
        self.output_label.text = res

    def feat_referral(self, instance):
        res = self.referral_engine.get_invite_info()
        self.output_label.text = res

    def feat_ar_camera(self, instance):
        res = handle_ar_camera()
        self.output_label.text = res

    def feat_slang_decoder(self, instance):
        txt = self.input_field.text.strip() or "Break a leg"
        res = handle_slang(txt)
        self.output_label.text = res

    def feat_offline_mode(self, instance):
        state = self.offline_engine.toggle()
        status = "ACTIVE" if state else "DISABLED"
        self.output_label.text = f"Offline Engine: [b]{status}[/b]"

    def feat_travel_sos(self, instance):
        res = handle_travel_sos(10)
        self.output_label.text = res

    def feat_doc_summarizer(self, instance):
        txt = self.input_field.text.strip()
        res = summarize_doc(txt)
        self.output_label.text = res

if __name__ == '__main__':
    LingoLensApp().run()
