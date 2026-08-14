import os
import sys
import json
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
import requests

# =====================================================================
# 1. შრიფტის მოძიება და გლობალური რეგისტრაცია (Kivy UI)
# =====================================================================
GEORGIAN_FONT = None

# ვამოწმებთ ფაილის არსებობას პროექტის ძირში
font_file = "NotoSansGeorgian.ttf" if os.path.exists("NotoSansGeorgian.ttf") else "georgian.ttf"

if os.path.exists(font_file):
    LabelBase.register(name="GeorgianFont", fn_regular=font_file)
    GEORGIAN_FONT = "GeorgianFont"
elif platform == 'android':
    possible_fonts = [
        "/system/fonts/NotoSansGeorgian-Regular.ttf",
        "/system/fonts/NotoSansGeorgian-VF.ttf",
        "/system/fonts/DroidSansGeorgian.ttf"
    ]
    for font_path in possible_fonts:
        if os.path.exists(font_path):
            try:
                LabelBase.register(name="GeorgianFont", fn_regular=font_path)
                GEORGIAN_FONT = "GeorgianFont"
                break
            except Exception:
                pass

# 🔥 ავტომატურად გადავცემთ შრიფტს TextInput, Label და Button ელემენტებს
if GEORGIAN_FONT:
    Builder.load_string(f'''
<Label>:
    font_name: '{GEORGIAN_FONT}'
<TextInput>:
    font_name: '{GEORGIAN_FONT}'
<Button>:
    font_name: '{GEORGIAN_FONT}'
''')

# =====================================================================
# 2. Android ნატიური ფუნქციები (Jnius)
# =====================================================================
if platform == 'android':
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        RecognizerIntent = autoclass('android.speech.RecognizerIntent')
        SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
        Bundle = autoclass('android.os.Bundle')
        Settings = autoclass('android.provider.Settings')
        Uri = autoclass('android.net.Uri')
    except Exception as e:
        print(f"Android Interop Initialization Error: {e}")

# =====================================================================
# 3. აპლიკაციის ძირითადი ინტერფეისი
# =====================================================================
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        self.api_key = ""

        # Header Title
        self.title_label = Label(
            text="[b]LingoLens Live AI Ecosystem[/b]",
            markup=True,
            font_size='22sp',
            size_hint_y=0.08
        )
        self.add_widget(self.title_label)

        # Status & Streak Info Bar
        self.status_label = Label(
            text="Engine Ready! | Daily Streak: 1 Days | Unlocked Badges: 2",
            color=(0.2, 0.8, 0.2, 1),
            font_size='13sp',
            size_hint_y=0.05
        )
        self.add_widget(self.status_label)

        # Input Text Area (TextInput - ახლა უკვე ქართული შრიფტით)
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი ან გამოიყენეთ ხმოვანი/OCR თარგმნა...",
            multiline=True,
            size_hint_y=0.35,
            padding_x=10,
            padding_y=10,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            font_size='16sp'
        )
        self.add_widget(self.text_input)

        # Translation Output Box
        self.output_label = Label(
            text="[AI Translation Output Will Appear Here]",
            markup=True,
            font_size='16sp',
            size_hint_y=0.25,
            color=(0.9, 0.9, 0.9, 1)
        )
        self.add_widget(self.output_label)

        # Action Buttons Layout Grid
        controls_grid = GridLayout(cols=2, spacing=10, size_hint_y=0.2)

        self.btn_live = Button(text="Hands-Free Live", background_color=(0.1, 0.5, 0.2, 1))
        self.btn_bubble = Button(text="Floating Bubble", background_color=(0.1, 0.3, 0.5, 1))
        self.btn_bubble.bind(on_press=self.check_overlay_permission)

        self.btn_voice = Button(text="AI Voice Clone", background_color=(0.5, 0.1, 0.2, 1))
        self.btn_streaks = Button(text="Daily Streaks", background_color=(0.5, 0.3, 0.1, 1))

        controls_grid.add_widget(self.btn_live)
        controls_grid.add_widget(self.btn_bubble)
        controls_grid.add_widget(self.btn_voice)
        controls_grid.add_widget(self.btn_streaks)

        self.add_widget(controls_grid)

        # API Key Config Button
        self.btn_api = Button(
            text="Set Gemini API Key",
            size_hint_y=0.07,
            background_color=(0.3, 0.3, 0.3, 1)
        )
        self.btn_api.bind(on_press=self.open_api_popup)
        self.add_widget(self.btn_api)

    def check_overlay_permission(self, instance):
        if platform == 'android':
            try:
                activity = PythonActivity.mActivity
                if not Settings.canDrawOverlays(activity):
                    intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse(f"package:{activity.getPackageName()}")
                    )
                    activity.startActivity(intent)
                else:
                    self.status_label.text = "Floating Overlay Granted & Active!"
            except Exception as e:
                self.status_label.text = f"Overlay Error: {e}"
        else:
            self.status_label.text = "Overlay requires Android environment."

    def open_api_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        api_input = TextInput(
            hint_text="შეიყვანეთ Gemini API Key...",
            text=self.api_key,
            multiline=False
        )
        save_btn = Button(text="შენახვა", size_hint_y=0.4)

        content.add_widget(api_input)
        content.add_widget(save_btn)

        popup = Popup(
            title="Gemini API Key კონფიგურაცია",
            content=content,
            size_hint=(0.85, 0.4)
        )

        def save_key(btn_instance):
            self.api_key = api_input.text.strip()
            self.status_label.text = "API Key წარმატებით შეინახა!"
            popup.dismiss()

        save_btn.bind(on_press=save_key)
        popup.open()


class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro"
        return MainLayout()


if __name__ == '__main__':
    LingoLensApp().run()
