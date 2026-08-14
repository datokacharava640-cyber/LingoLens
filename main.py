import os
import sys
import traceback
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

# =====================================================================
# 1. შრიფტის უსაფრთხო ჩატვირთვა (ქართული ასოებისთვის - კუბიკების გარეშე)
# =====================================================================
GEORGIAN_FONT = None
font_file = "NotoSansGeorgian.ttf" if os.path.exists("NotoSansGeorgian.ttf") else "georgian.ttf"

if os.path.exists(font_file):
    try:
        LabelBase.register(name="GeorgianFont", fn_regular=font_file)
        GEORGIAN_FONT = "GeorgianFont"
    except Exception as e:
        print(f"Font Registration Error: {e}")

# Kivy UI ელემენტების შრიფტის ავტომატური მინიჭება
if GEORGIAN_FONT:
    try:
        Builder.load_string(f'''
<Label>:
    font_name: '{GEORGIAN_FONT}'
<TextInput>:
    font_name: '{GEORGIAN_FONT}'
<Button>:
    font_name: '{GEORGIAN_FONT}'
''')
    except Exception as e:
        print(f"KV Builder Error: {e}")

# =====================================================================
# 2. მთავარი ინტერფეისი
# =====================================================================
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        self.api_key = ""

        # Title
        self.title_label = Label(
            text="[b]LingoLens Live AI Ecosystem[/b]",
            markup=True,
            font_size='22sp',
            size_hint_y=0.08
        )
        self.add_widget(self.title_label)

        # Status
        self.status_label = Label(
            text="Engine Ready! | System Active",
            color=(0.2, 0.8, 0.2, 1),
            font_size='13sp',
            size_hint_y=0.05
        )
        self.add_widget(self.status_label)

        # Input Field (TextInput - ქართული ასოებით)
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი აქ...",
            multiline=True,
            size_hint_y=0.35,
            padding_x=10,
            padding_y=10,
            font_size='16sp'
        )
        self.add_widget(self.text_input)

        # Output Text
        self.output_label = Label(
            text="[AI თარგმანი გამოჩნდება აქ]",
            markup=True,
            font_size='16sp',
            size_hint_y=0.25
        )
        self.add_widget(self.output_label)

        # Buttons Grid
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

        # API Key Button
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
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Settings = autoclass('android.provider.Settings')
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')

                activity = PythonActivity.mActivity
                if not Settings.canDrawOverlays(activity):
                    intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse(f"package:{activity.getPackageName()}")
                    )
                    activity.startActivity(intent)
                else:
                    self.status_label.text = "Floating Overlay Granted!"
            except Exception as e:
                self.status_label.text = f"Overlay Error: {e}"
        else:
            self.status_label.text = "Requires Android environment."

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
            title="API Key კონფიგურაცია",
            content=content,
            size_hint=(0.85, 0.4)
        )

        def save_key(btn_instance):
            self.api_key = api_input.text.strip()
            self.status_label.text = "API Key შენახულია!"
            popup.dismiss()

        save_btn.bind(on_press=save_key)
        popup.open()


class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro"
        return MainLayout()

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.request_permissions_safe, 1)

    def request_permissions_safe(self, dt):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
        except Exception as e:
            print(f"Permission Request Log: {e}")


if __name__ == '__main__':
    try:
        LingoLensApp().run()
    except Exception as fatal_error:
        print("Fatal Crash Captured:")
        traceback.print_exc()
