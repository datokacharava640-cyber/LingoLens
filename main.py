import sys
import os
import json
import ssl
import threading
import urllib.request
from urllib.parse import quote

# Kivy & KivyMD Setup
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.utils import platform, get_color_from_hex

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.menu import MDDropdownMenu

# ---------------------------------------------------------
# 1. PERMISSION MANAGER (ANDROID NATIVE)
# ---------------------------------------------------------
def request_android_permissions():
    if platform == 'android':
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
        except Exception as e:
            print(f"Permissions error: {e}")

# ---------------------------------------------------------
# 2. UI LAYOUT (KV LANGUAGE)
# ---------------------------------------------------------
KV = '''
MDScreen:
    md_bg_color: 0.07, 0.08, 0.12, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "12dp"
        spacing: "10dp"

        # Top Bar
        MDBoxLayout:
            size_hint_y: None
            height: "50dp"
            spacing: "10dp"

            MDLabel:
                text: "LingoLens Ultra Pro"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.3, 0.65, 1, 1

            MDIconButton:
                icon: "camera"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.8, 1, 1
                on_release: app.open_camera()

            MDIconButton:
                icon: "layers-triple"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.8, 1, 1
                on_release: app.request_overlay()

            MDIconButton:
                icon: "dots-vertical"
                theme_icon_color: "Custom"
                icon_color: 1, 1, 1, 1
                on_release: app.open_settings_menu(self)

        # Language Selector Bar
        MDBoxLayout:
            size_hint_y: None
            height: "48dp"
            spacing: "8dp"

            MDRectangleFlatButton:
                id: btn_src_lang
                text: "ქართული"
                size_hint_x: 0.4
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                line_color: 0.3, 0.35, 0.45, 1
                on_release: app.open_lang_menu(self, 'source')

            MDIconButton:
                icon: "swap-horizontal"
                theme_icon_color: "Custom"
                icon_color: 0.3, 0.65, 1, 1
                on_release: app.swap_languages()

            MDRectangleFlatButton:
                id: btn_trg_lang
                text: "English"
                size_hint_x: 0.4
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                line_color: 0.3, 0.35, 0.45, 1
                on_release: app.open_lang_menu(self, 'target')

        # Real-time Input Area
        MDCard:
            size_hint_y: 0.3
            md_bg_color: 0.12, 0.14, 0.18, 1
            radius: [12,]
            padding: "10dp"

            MDTextField:
                id: input_field
                hint_text: "შეიყვანეთ ტექსტი ან გამოიყენეთ ხმა..."
                multiline: True
                max_height: "120dp"
                active_line_color: 0.3, 0.65, 1, 1
                text_color_normal: 1, 1, 1, 1
                hint_text_color_normal: 0.5, 0.55, 0.65, 1

        # Real-time Output Area
        MDCard:
            size_hint_y: 0.3
            md_bg_color: 0.12, 0.14, 0.18, 1
            radius: [12,]
            padding: "12dp"
            orientation: 'vertical'

            MDLabel:
                id: output_field
                text: "ნათარგმნი ტექსტი (Real-Time)..."
                theme_text_color: "Custom"
                text_color: 0, 1, 0.78, 1
                font_style: "Body1"

            MDBoxLayout:
                size_hint_y: None
                height: "40dp"
                alignment: "right"

                MDIconButton:
                    icon: "volume-high"
                    theme_icon_color: "Custom"
                    icon_color: 0, 1, 0.78, 1
                    on_release: app.speak_output()

        # Real-time Dual Speech Control
        MDBoxLayout:
            size_hint_y: 0.15
            spacing: "12dp"

            MDRaisedButton:
                text: "საუბარი (მარცხენა)"
                size_hint_x: 0.5
                md_bg_color: 0.03, 0.5, 0.9, 1
                on_release: app.start_voice_stream('source')

            MDRaisedButton:
                text: "საუბარი (მარჯვენა)"
                size_hint_x: 0.5
                md_bg_color: 0, 0.7, 0.55, 1
                on_release: app.start_voice_stream('target')
'''

LANGUAGES = {
    "English": "en",
    "ქართული": "ka",
    "Русский": "ru",
    "Türkçe": "tr",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Italiano": "it"
}

# ---------------------------------------------------------
# 3. MAIN APPLICATION CLASS
# ---------------------------------------------------------
class LingoLensPro(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.dialog = None
        self.src_lang_code = "ka"
        self.trg_lang_code = "en"

    def build(self):
        request_android_permissions()
        return Builder.load_string(KV)

    def open_lang_menu(self, caller, target_type):
        menu_items = [
            {
                "text": lang,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=lang: self.set_language(x, target_type),
            } for lang in LANGUAGES.keys()
        ]
        self.menu = MDDropdownMenu(
            caller=caller,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    def set_language(self, lang_name, target_type):
        if target_type == 'source':
            self.root.ids.btn_src_lang.text = lang_name
            self.src_lang_code = LANGUAGES[lang_name]
        else:
            self.root.ids.btn_trg_lang.text = lang_name
            self.trg_lang_code = LANGUAGES[lang_name]
        self.menu.dismiss()

    def swap_languages(self):
        tmp_text = self.root.ids.btn_src_lang.text
        self.root.ids.btn_src_lang.text = self.root.ids.btn_trg_lang.text
        self.root.ids.btn_trg_lang.text = tmp_text
        
        self.src_lang_code, self.trg_lang_code = self.trg_lang_code, self.src_lang_code

    def start_voice_stream(self, side):
        # ეტაპი 2: ჩაშენდება Google ML Kit Speech-to-Text Stream
        lang = self.src_lang_code if side == 'source' else self.trg_lang_code
        self.show_popup("ხმის ჩაწერა", f"მზადყოფნა რეალურ დროში მოსასმენად ({lang})...")

    def open_camera(self):
        # ეტაპი 3: ჩაშენდება Google ML Kit On-Device OCR Camera Stream
        self.show_popup("კამერა", "მზადდება Google ML Kit Live OCR კამერა...")

    def request_overlay(self):
        # ეტაპი 4: Floating Window Service
        self.show_popup("Overlay", "მცურავი ფანჯრის სერვისის გაშვება...")

    def speak_output(self):
        # Azure TTS Integration
        text = self.root.ids.output_field.text
        if text:
            self.show_popup("TTS", "ტექსტის გაჟღერება...")

    def open_settings_menu(self, caller):
        pass

    def show_popup(self, title, text):
        if not self.dialog:
            self.dialog = MDDialog(
                title=title,
                text=text,
                buttons=[MDRaisedButton(text="OK", on_release=lambda x: self.dialog.dismiss())]
            )
        else:
            self.dialog.title = title
            self.dialog.text = text
        self.dialog.open()

if __name__ == "__main__":
    LingoLensPro().run()
