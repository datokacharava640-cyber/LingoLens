import os
import sys
import traceback

# 1. გლობალური შეცდომების დამჭერი (Crash Interceptor)
CRASH_LOG = None

def global_exception_handler(exc_type, exc_value, exc_traceback):
    global CRASH_LOG
    CRASH_LOG = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("FATAL CRASH DETECTED:\n", CRASH_LOG)

sys.excepthook = global_exception_handler

# 2. Kivy-ს უსაფრთხო იმპორტი
try:
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
    from kivy.uix.scrollview import ScrollView
    from kivy.clock import Clock
except Exception as import_err:
    CRASH_LOG = f"Kivy Core Import Error:\n{traceback.format_exc()}"

# 3. შრიფტის უსაფრთხო რეგისტრაცია
GEORGIAN_FONT = None
font_file = "NotoSansGeorgian.ttf" if os.path.exists("NotoSansGeorgian.ttf") else "georgian.ttf"

if os.path.exists(font_file):
    try:
        LabelBase.register(name="GeorgianFont", fn_regular=font_file)
        GEORGIAN_FONT = "GeorgianFont"
    except Exception as font_err:
        print(f"Font Error: {font_err}")

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
    except Exception as kv_err:
        print(f"KV Load Error: {kv_err}")

# 4. შეცდომის გამოჩენის ინტერფეისი (თუ აპლიკაცია ფუჭდება)
class ErrorScreen(ScrollView):
    def __init__(self, error_msg, **kwargs):
        super().__init__(**kwargs)
        self.padding = 20
        lbl = Label(
            text=f"[color=ff3333][b]⚠️ LINGOLENS ERROR LOG ⚠️[/b][/color]\n\n{error_msg}",
            markup=True,
            font_size='14sp',
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        lbl.bind(texture_size=lambda instance, value: setattr(instance, 'size', value))
        self.add_widget(lbl)

# 5. აპლიკაციის ძირითადი ინტერფეისი
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        self.api_key = ""

        # Title
        self.title_label = Label(
            text="[b]LingoLens Ultra Pro[/b]",
            markup=True,
            font_size='22sp',
            size_hint_y=0.08
        )
        self.add_widget(self.title_label)

        # Status
        self.status_label = Label(
            text="Engine Active | System Ready",
            color=(0.2, 0.8, 0.2, 1),
            font_size='13sp',
            size_hint_y=0.05
        )
        self.add_widget(self.status_label)

        # Input Box
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი აქ...",
            multiline=True,
            size_hint_y=0.35,
            padding_x=10,
            padding_y=10,
            font_size='16sp'
        )
        self.add_widget(self.text_input)

        # Output Box
        self.output_label = Label(
            text="[AI თარგმანი გამოჩნდება აქ]",
            markup=True,
            font_size='16sp',
            size_hint_y=0.25
        )
        self.add_widget(self.output_label)

        # Controls Grid
        controls_grid = GridLayout(cols=2, spacing=10, size_hint_y=0.2)

        self.btn_live = Button(text="Hands-Free Live", background_color=(0.1, 0.5, 0.2, 1))
        self.btn_bubble = Button(text="Floating Bubble", background_color=(0.1, 0.3, 0.5, 1))
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
        # თუ თავშივე მოხდა კრიტიკული შეცდომა, ვაჩვენებთ ერორს ეკრანზე
        if CRASH_LOG:
            return ErrorScreen(CRASH_LOG)

        try:
            return MainLayout()
        except Exception as e:
            return ErrorScreen(traceback.format_exc())


if __name__ == '__main__':
    try:
        LingoLensApp().run()
    except Exception as fatal_e:
        print("Crash outside Kivy App loop:")
        traceback.print_exc()
