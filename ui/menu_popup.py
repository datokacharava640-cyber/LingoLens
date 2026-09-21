from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import config

class MenuPopup(Popup):
    def __init__(self, academic_cb, grammar_cb, **kwargs):
        super().__init__(**kwargs)
        # ამოღებულია Emoji, რათა არ გამოჩნდეს ოთხკუთხედები
        self.title = "LingoLens Menu"
        self.title_font = config.FONT_PATH
        self.size_hint = (0.85, 0.45)
        
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        btn_academic = Button(
            text="Academic AI Rewrite", 
            font_name=config.FONT_PATH,
            size_hint_y=0.4
        )
        btn_grammar = Button(
            text="Grammar Check & Explain", 
            font_name=config.FONT_PATH,
            size_hint_y=0.4
        )
        
        btn_academic.bind(on_release=lambda x: (academic_cb(), self.dismiss()))
        btn_grammar.bind(on_release=lambda x: (grammar_cb(), self.dismiss()))
        
        layout.add_widget(btn_academic)
        layout.add_widget(btn_grammar)
        self.content = layout
