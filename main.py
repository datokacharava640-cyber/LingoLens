from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

import config
from utils.translator import translate_text
from utils.tts_engine import speak
from ui.camera_widget import RotatedCameraWidget

class LingoLensApp(App):
    def build(self):
        self.src_lang = "ka"
        self.target_lang = "en"

        main_layout = BoxLayout(orientation='vertical', spacing=6, padding=8)

        # Header
        header = BoxLayout(size_hint_y=0.08, spacing=5)
        title_label = Label(text="LingoLens AI", font_size='20sp', color=(0, 1, 0, 1), bold=True, font_name=config.FONT_PATH)
        header.add_widget(title_label)
        main_layout.add_widget(header)

        # Language Selectors
        lang_layout = BoxLayout(size_hint_y=0.08, spacing=5)
        self.spin_src = Spinner(text="KA", values=config.LANG_NAMES, font_name=config.FONT_PATH)
        self.spin_target = Spinner(text="EN", values=config.LANG_NAMES, font_name=config.FONT_PATH)
        self.spin_src.bind(text=self.on_src_change)
        self.spin_target.bind(text=self.on_target_change)
        
        lang_layout.add_widget(self.spin_src)
        lang_layout.add_widget(self.spin_target)
        main_layout.add_widget(lang_layout)

        # Text Inputs
        self.input_text = TextInput(hint_text="ჩაწერეთ ტექსტი...", size_hint_y=0.25, font_name=config.FONT_PATH)
        self.input_text.bind(text=self.on_text_type)
        self.output_text = TextInput(hint_text="თარგმანი...", size_hint_y=0.25, readonly=True, font_name=config.FONT_PATH)

        main_layout.add_widget(self.input_text)
        main_layout.add_widget(self.output_text)

        # TTS Buttons
        btn_speak = Button(text="🔊 მოსმენა", size_hint_y=0.08, font_name=config.FONT_PATH, on_press=self.handle_tts)
        main_layout.add_widget(btn_speak)

        self.status_label = Label(text="სისტემა მზადაა", size_hint_y=0.05, font_name=config.FONT_PATH)
        main_layout.add_widget(self.status_label)

        return main_layout

    def on_src_change(self, spinner, text):
        self.src_lang = config.LANGUAGES.get(text, "ka")

    def on_target_change(self, spinner, text):
        self.target_lang = config.LANGUAGES.get(text, "en")

    def on_text_type(self, instance, value):
        if value.strip():
            prompt = f"Translate from {self.src_lang} to {self.target_lang}: {value}"
            translate_text(
                prompt, value, self.src_lang, self.target_lang,
                lambda res: Clock.schedule_once(lambda dt: self.update_output(res))
            )

    def update_output(self, text):
        if text:
            self.output_text.text = text

    def handle_tts(self, instance):
        speak(self.output_text.text, self.target_lang, self.user_data_dir, lambda msg: setattr(self.status_label, 'text', msg))

if __name__ == "__main__":
    LingoLensApp().run()
