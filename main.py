import os
import threading
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.utils import platform

# Android Permissions
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.CAMERA,
        Permission.RECORD_AUDIO,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE
    ])

# ⚠️ Chasvi sheni moqmedi Gemini API Key
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

class LingoLensApp(App):
    def build(self):
        self.src_lang = "ka"
        self.target_lang = "en"
        self.camera_active = False

        main_layout = BoxLayout(orientation='vertical', spacing=8, padding=10)

        # 1. Header (Tavsart'i da Meniu-s ghilaki)
        header = BoxLayout(size_hint_y=0.08, spacing=5)
        title_label = Label(
            text="LingoLens AI",
            font_size='20sp',
            color=(0, 1, 0, 1),
            bold=True,
            halign='left',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))
        
        btn_menu = Button(
            text="⚙️ Meniu",
            size_hint_x=0.3,
            background_color=(0.3, 0.3, 0.8, 1),
            on_press=self.open_menu_popup
        )
        
        header.add_widget(title_label)
        header.add_widget(btn_menu)
        main_layout.add_widget(header)

        # 2. Enis archeva da Swap (Language Bar)
        lang_layout = BoxLayout(size_hint_y=0.08, spacing=5)
        self.btn_src = Button(text=f"A: {self.src_lang.upper()}", on_press=self.toggle_src_lang)
        self.btn_swap = Button(text="🔄 Swap", background_color=(0.1, 0.4, 0.6, 1), on_press=self.swap_languages)
        self.btn_target = Button(text=f"B: {self.target_lang.upper()}", on_press=self.toggle_target_lang)
        
        lang_layout.add_widget(self.btn_src)
        lang_layout.add_widget(self.btn_swap)
        lang_layout.add_widget(self.btn_target)
        main_layout.add_widget(lang_layout)

        # 3. Ormxrivi Dialogi (Speaker A / B Live Audio)
        speaker_layout = BoxLayout(size_hint_y=0.15, spacing=8)
        self.btn_speaker_a = Button(
            text=f"🎙️ [{self.src_lang.upper()}] Speaker A\n(Saubari)",
            background_color=(0.1, 0.6, 0.3, 1),
            halign='center',
            on_press=lambda x: self.start_live_dialogue("speaker_a")
        )
        self.btn_speaker_b = Button(
            text=f"🎙️ [{self.target_lang.upper()}] Speaker B\n(Saubari)",
            background_color=(0.7, 0.2, 0.2, 1),
            halign='center',
            on_press=lambda x: self.start_live_dialogue("speaker_b")
        )
        speaker_layout.add_widget(self.btn_speaker_a)
        speaker_layout.add_widget(self.btn_speaker_b)
        main_layout.add_widget(speaker_layout)

        # 4. SMS Targmani / Teqsti (Input & Output Boxes)
        self.input_text = TextInput(
            hint_text="Chatsere't SMS, teqsti an khmovani sheqt'yobineba...",
            size_hint_y=0.3,
            multiline=True
        )
        self.output_text = TextInput(
            hint_text="Targmani da pasukhi gamochnde'ba ak...",
            size_hint_y=0.3,
            readonly=True,
            multiline=True
        )
        main_layout.add_widget(self.input_text)
        main_layout.add_widget(self.output_text)

        # Status Footer
        self.status_label = Label(text="Sist'ema mzadaa SMS/Dialogistvis", size_hint_y=0.04, color=(0.7, 0.7, 0.7, 1))
        main_layout.add_widget(self.status_label)

        return main_layout

    # --- MENIU POPUP (Kvela danarcheni punqtsia) ---
    def open_menu_popup(self, instance):
        menu_content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Camera Placeholder in Menu (Tu kameras vartavt)
        self.camera_box = BoxLayout(size_hint_y=0.4)
        self.camera_placeholder = Label(text="📷 Kamera gatishulia.")
        self.camera_box.add_widget(self.camera_placeholder)
        menu_content.add_widget(self.camera_box)

        # Buttons Grid inside Menu
        menu_grid = GridLayout(cols=2, spacing=8, size_hint_y=0.5)
        
        menu_grid.add_widget(Button(text="📷 Toggle Cam", on_press=self.toggle_camera))
        menu_grid.add_widget(Button(text="🔍 Live OCR", on_press=self.run_ocr))
        menu_grid.add_widget(Button(text="🎓 Academic AI", on_press=self.academic_ai))
        menu_grid.add_widget(Button(text="📚 Grammar", on_press=self.explain_grammar))
        menu_grid.add_widget(Button(text="🔊 Read Text", on_press=self.read_text))
        menu_grid.add_widget(Button(text="📋 Copy Text", on_press=self.copy_text))
        menu_grid.add_widget(Button(text="📜 History", on_press=self.show_history))
        menu_grid.add_widget(Button(text="🗑️ Clear All", on_press=self.clear_all))

        menu_content.add_widget(menu_grid)

        # Close Menu Button
        btn_close = Button(text="❌ Dakhurva", size_hint_y=0.1, background_color=(0.8, 0.2, 0.2, 1))
        menu_content.add_widget(btn_close)

        popup = Popup(
            title="Shesazleblobebi & Damat'ebiti Funqtstsebi",
            content=menu_content,
            size_hint=(0.9, 0.85)
        )
        btn_close.bind(on_press=popup.dismiss)
        popup.open()

    # --- ENANAKIS DYNAMIQUE UPDATE ---
    def update_speaker_labels(self):
        self.btn_src.text = f"A: {self.src_lang.upper()}"
        self.btn_target.text = f"B: {self.target_lang.upper()}"
        self.btn_speaker_a.text = f"🎙️ [{self.src_lang.upper()}] Speaker A\n(Saubari)"
        self.btn_speaker_b.text = f"🎙️ [{self.target_lang.upper()}] Speaker B\n(Saubari)"

    def swap_languages(self, instance):
        self.src_lang, self.target_lang = self.target_lang, self.src_lang
        self.update_speaker_labels()

    def toggle_src_lang(self, instance):
        self.src_lang = "en" if self.src_lang == "ka" else "ka"
        self.update_speaker_labels()

    def toggle_target_lang(self, instance):
        self.target_lang = "en" if self.target_lang == "ka" else "ka"
        self.update_speaker_labels()

    # --- LIVE DIALOGUE & SMS TRANSLATION ---
    def start_live_dialogue(self, mode):
        from_l = self.src_lang if mode == "speaker_a" else self.target_lang
        to_l = self.target_lang if mode == "speaker_a" else self.src_lang
        speaker_name = "Speaker A" if mode == "speaker_a" else "Speaker B"

        text = self.input_text.text.strip()
        if not text:
            self.status_label.text = f"🎙️ [{speaker_name}] Chachere't teqsti SMS velshi!"
            return

        prompt = f"Real-time dialogue translation from {from_l} to {to_l}: '{text}'"
        self.call_gemini_api(prompt, auto_speak=True, target_lang=to_l)

    def call_gemini_api(self, prompt, auto_speak=False, target_lang="en"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                translated_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                self.output_text.text = translated_text
                self.status_label.text = "✅ Targmani mzadaa"

                if auto_speak:
                    self.speak_text(translated_text, target_lang)
            else:
                self.output_text.text = f"API Error: {response.status_code}\nSheamotsme't GEMINI_API_KEY."
        except Exception as e:
            self.output_text.text = f"Network Error: {str(e)}"

    def speak_text(self, text, lang):
        try:
            from plyer import tts
            tts.speak(text)
        except Exception:
            self.status_label.text = "🔊 TTS miutsvdome'lia"

    # --- MENU FUNCTIONS ---
    def toggle_camera(self, instance):
        if not self.camera_active:
            try:
                self.camera_box.clear_widgets()
                self.camera_obj = Camera(play=True, resolution=(640, 480))
                self.camera_box.add_widget(self.camera_obj)
                self.camera_active = True
                self.status_label.text = "📷 Kamera chartulia"
            except Exception as e:
                self.status_label.text = f"Kamera error: {str(e)}"
        else:
            self.camera_box.clear_widgets()
            self.camera_box.add_widget(self.camera_placeholder)
            self.camera_active = False
            self.status_label.text = "📷 Kamera gatishulia"

    def academic_ai(self, instance):
        text = self.input_text.text.strip()
        if text:
            self.call_gemini_api(f"Rewrite in formal academic tone: {text}")

    def explain_grammar(self, instance):
        text = self.input_text.text.strip()
        if text:
            self.call_gemini_api(f"Explain grammar step-by-step: {text}")

    def clear_all(self, instance):
        self.input_text.text = ""
        self.output_text.text = ""
        self.status_label.text = "Gasuptavebulia"

    def copy_text(self, instance):
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(self.output_text.text)
        self.status_label.text = "Copied!"

    def read_text(self, instance):
        if self.output_text.text:
            self.speak_text(self.output_text.text, self.target_lang)

    def run_ocr(self, instance):
        self.status_label.text = "🔍 OCR processing..."

    def show_history(self, instance):
        self.output_text.text = "📜 Istoria tsarjelia."

if __name__ == "__main__":
    LingoLensApp().run()
