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
from ui.menu_popup import MenuPopup

class LingoLensApp(App):
    def build(self):
        self.src_lang = "ka"
        self.target_lang = "en"
        self.debounce_event = None

        main_layout = BoxLayout(orientation='vertical', spacing=6, padding=8)

        # 1. Header (სათაური და მენიუ)
        header = BoxLayout(size_hint_y=0.08, spacing=5)
        title_label = Label(
            text="LingoLens AI", 
            font_size='20sp', 
            color=(0, 1, 0, 1), 
            bold=True, 
            font_name=config.FONT_PATH
        )
        btn_menu = Button(
            text="☰ მენიუ", 
            size_hint_x=0.3, 
            font_name=config.FONT_PATH,
            on_press=self.open_menu
        )
        header.add_widget(title_label)
        header.add_widget(btn_menu)
        main_layout.add_widget(header)

        # 2. ენების არჩევა + SWAP (🔄)
        lang_layout = BoxLayout(size_hint_y=0.08, spacing=5)
        self.spin_src = Spinner(text="KA", values=config.LANG_NAMES, font_name=config.FONT_PATH)
        self.btn_swap = Button(text="🔄", size_hint_x=0.2, font_name=config.FONT_PATH, on_press=self.swap_languages)
        self.spin_target = Spinner(text="EN", values=config.LANG_NAMES, font_name=config.FONT_PATH)
        
        self.spin_src.bind(text=self.on_src_change)
        self.spin_target.bind(text=self.on_target_change)
        
        lang_layout.add_widget(self.spin_src)
        lang_layout.add_widget(self.btn_swap)
        lang_layout.add_widget(self.spin_target)
        main_layout.add_widget(lang_layout)

        # 3. ტექსტის შეყვანა და თარგმანი
        self.input_text = TextInput(
            hint_text="ჩაწერეთ ტექსტი...", 
            size_hint_y=0.25, 
            font_name=config.FONT_PATH,
            multiline=True
        )
        self.input_text.bind(text=self.on_text_type)
        
        self.output_text = TextInput(
            hint_text="თარგმანი...", 
            size_hint_y=0.25, 
            readonly=True, 
            font_name=config.FONT_PATH,
            multiline=True
        )

        main_layout.add_widget(self.input_text)
        main_layout.add_widget(self.output_text)

        # 4. ღილაკების პანელი (მოსმენა, კოპირება, გასუფთავება)
        tools_grid = GridLayout(cols=3, size_hint_y=0.08, spacing=5)
        
        btn_speak = Button(text="🔊 მოსმენა", font_name=config.FONT_PATH, on_press=self.handle_tts)
        btn_copy = Button(text="📋 კოპირება", font_name=config.FONT_PATH, on_press=self.copy_output)
        btn_clear = Button(text="🗑️ გასუფთავება", font_name=config.FONT_PATH, on_press=self.clear_all)

        tools_grid.add_widget(btn_speak)
        tools_grid.add_widget(btn_copy)
        tools_grid.add_widget(btn_clear)
        main_layout.add_widget(tools_grid)

        # 5. სტატუსის ბარი
        self.status_label = Label(
            text="სისტემა მზადაა", 
            size_hint_y=0.05, 
            font_name=config.FONT_PATH,
            color=(0.8, 0.8, 0.8, 1)
        )
        main_layout.add_widget(self.status_label)

        return main_layout

    # ენების შეცვლა
    def on_src_change(self, spinner, text):
        self.src_lang = config.LANGUAGES.get(text, "ka")
        self.trigger_translation()

    def on_target_change(self, spinner, text):
        self.target_lang = config.LANGUAGES.get(text, "en")
        self.trigger_translation()

    def swap_languages(self, instance):
        src_text = self.spin_src.text
        self.spin_src.text = self.spin_target.text
        self.spin_target.text = src_text

    # ავტომატური თარგმანი ტექსტის აკრეფისას (Debounce 0.8 წამი)
    def on_text_type(self, instance, value):
        if self.debounce_event:
            self.debounce_event.cancel()
        self.debounce_event = Clock.schedule_once(lambda dt: self.trigger_translation(), 0.8)

    def trigger_translation(self):
        val = self.input_text.text.strip()
        if not val:
            self.output_text.text = ""
            return
        
        self.status_label.text = "⏳ ითარგმნება..."
        prompt = f"Translate accurately from {self.src_lang} to {self.target_lang}: {val}"
        
        translate_text(
            prompt, val, self.src_lang, self.target_lang,
            lambda res: Clock.schedule_once(lambda dt: self.update_output(res))
        )

    def update_output(self, text):
        self.output_text.text = text if text else "შეცდომა თარგმნისას"
        self.status_label.text = "✅ მზადაა"

    # ხმოვანი გაჟღერება
    def handle_tts(self, instance):
        text_to_speak = self.output_text.text.strip() or self.input_text.text.strip()
        lang_to_use = self.target_lang if self.output_text.text.strip() else self.src_lang
        
        speak(
            text_to_speak, 
            lang_to_use, 
            self.user_data_dir, 
            lambda msg: Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', msg))
        )

    # ინსტრუმენტები
    def copy_output(self, instance):
        if self.output_text.text:
            Clipboard.copy(self.output_text.text)
            self.status_label.text = "📋 ტექსტი დაკოპირდა!"

    def clear_all(self, instance):
        self.input_text.text = ""
        self.output_text.text = ""
        self.status_label.text = "🧹 გასუფთავებულია"

    # მენიუ
    def open_menu(self, instance):
        MenuPopup(self.run_academic, self.run_grammar).open()

    def run_academic(self):
        val = self.input_text.text.strip()
        if val:
            self.status_label.text = "🎓 აკადემიური დამუშავება..."
            prompt = f"Rewrite this text in an academic professional tone in {self.target_lang}: {val}"
            translate_text(prompt, val, self.src_lang, self.target_lang, lambda res: Clock.schedule_once(lambda dt: self.update_output(res)))

    def run_grammar(self):
        val = self.input_text.text.strip()
        if val:
            self.status_label.text = "📚 გრამატიკის შემოწმება..."
            prompt = f"Correct grammar and explain mistakes briefly in {self.target_lang} for: {val}"
            translate_text(prompt, val, self.src_lang, self.target_lang, lambda res: Clock.schedule_once(lambda dt: self.update_output(res)))

if __name__ == "__main__":
    LingoLensApp().run()
