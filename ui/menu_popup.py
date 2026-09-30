# ==========================================
# LingoLens AI - Menu Popup UI
# ==========================================

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
import config


class MenuPopup(Popup):

  def __init__(self, academic_cb, grammar_cb, **kwargs):
    super().__init__(**kwargs)
    self.title = "LingoLens Menu"
    self.title_font = getattr(config, "FONT_PATH", None)
    self.size_hint = (0.85, 0.5)

    layout = BoxLayout(orientation="vertical", spacing=10, padding=15)

    btn_academic = Button(
        text="Academic AI Rewrite",
        font_name=getattr(config, "FONT_PATH", None),
        size_hint_y=0.35,
    )
    btn_grammar = Button(
        text="Grammar Check & Explain",
        font_name=getattr(config, "FONT_PATH", None),
        size_hint_y=0.35,
    )

    # დახურვის ღილაკი
    btn_close = Button(
        text="გასვლა / Close",
        font_name=getattr(config, "FONT_PATH", None),
        size_hint_y=0.3,
        background_color=(0.8, 0.2, 0.2, 1),
    )

    btn_academic.bind(on_release=lambda x: (academic_cb(), self.dismiss()))
    btn_grammar.bind(on_release=lambda x: (grammar_cb(), self.dismiss()))
    btn_close.bind(on_release=self.dismiss)

    layout.add_widget(btn_academic)
    layout.add_widget(btn_grammar)
    layout.add_widget(btn_close)

    self.content = layout
