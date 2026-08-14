import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

# 4 ვირუსული მოდულის იმპორტი
from modules.floating_bubble import FloatingBubbleService
from modules.streak_system import StreakTracker
from modules.referral_system import ReferralEngine
from modules.voice_clone import VoiceCloner

class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro"

        # მოდულების ინიციალიზაცია
        self.bubble_svc = FloatingBubbleService()
        self.streak_tracker = StreakTracker()
        self.referral_engine = ReferralEngine()
        self.voice_cloner = VoiceCloner()

        root = BoxLayout(orientation='vertical', padding=12, spacing=8)

        # Header Title
        header = Label(
            text="[b]✨ LingoLens Viral AI[/b]",
            markup=True,
            font_size='22sp',
            size_hint_y=0.08
        )
        root.add_widget(header)

        # Status Bar
        self.status_label = Label(
            text=f"🟢 Status: Ready | {self.streak_tracker.get_status()}",
            font_size='13sp',
            size_hint_y=0.08,
            color=(0.2, 0.8, 0.2, 1)
        )
        root.add_widget(self.status_label)

        # Input Area
        self.input_field = TextInput(
            hint_text="Enter text, phrase, or speak...",
            multiline=True,
            size_hint_y=0.20
        )
        root.add_widget(self.input_field)

        # Output Display
        self.output_label = Label(
            text="[Feature Output Will Appear Here]",
            markup=True,
            size_hint_y=0.24
        )
        root.add_widget(self.output_label)

        # Control Panel Grid (4 Core Features)
        scroll = ScrollView(size_hint_y=0.40)
        grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        btn_specs = [
            ("🎈 Floating Screen Bubble", self.feat_toggle_bubble, (0.2, 0.6, 1, 1)),
            ("🗣️ AI Voice Cloning Translate", self.feat_voice_clone, (0.9, 0.3, 0.5, 1)),
            ("🔥 Streaks & Daily Progress", self.feat_check_streak, (0.9, 0.5, 0.1, 1)),
            ("🎁 Invite Friends & Get Rewards", self.feat_referral, (0.2, 0.8, 0.4, 1))
        ]

        for text, callback, color in btn_specs:
            btn = Button(
                text=text,
                size_hint_y=None,
                height=55,
                background_color=color,
                font_size='14sp'
            )
            btn.bind(on_press=callback)
            grid.add_widget(btn)

        scroll.add_widget(grid)
        root.add_widget(scroll)

        return root

    def feat_toggle_bubble(self, instance):
        res = self.bubble_svc.toggle_bubble()
        self.output_label.text = res
        self.status_label.text = "🎈 Floating Bubble Updated"

    def feat_voice_clone(self, instance):
        txt = self.input_field.text.strip() or "Hello, this is my AI cloned voice."
        res = self.voice_cloner.translate_in_custom_voice(txt)
        self.output_label.text = res
        self.status_label.text = "🗣️ Voice Clone Active"

    def feat_check_streak(self, instance):
        res = self.streak_tracker.record_activity()
        self.output_label.text = res
        self.status_label.text = f"🟢 Status: {self.streak_tracker.get_status()}"

    def feat_referral(self, instance):
        res = self.referral_engine.get_invite_info()
        self.output_label.text = res
        self.status_label.text = "🎁 Referral System Loaded"

if __name__ == '__main__':
    LingoLensApp().run()
