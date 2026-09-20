import os
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.popup import Popup
from kivy.utils import platform

# --- შენი რეპოზიტორიიდან ფაილების იმპორტი ---
try:
    import config
except ImportError:
    config = None

try:
    import languages
except ImportError:
    languages = None

try:
    import offline_engine
except ImportError:
    offline_engine = None

# Android Permissions
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.CAMERA,
        Permission.RECORD_AUDIO,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE
    ])

# 🔐 API Key და Vercel Endpoint-ის დეკოდირება
def _decode_key(cipher_data):
    salt = "LingoLensSecret2026"
    return bytearray([b ^ ord(salt[i % len(salt)]) for i, b in enumerate(cipher_data)]).decode('utf-8')

API_ENDPOINT = _decode_key([
    68, 82, 11, 114, 119, 107, 107, 81, 105, 114, 118, 22, 114, 87, 80, 117,
    112, 112, 120, 104, 119, 107, 102, 102, 115, 115, 126, 112, 105, 101, 100,
    119, 115, 87, 102, 115, 80, 120, 107, 123, 114, 122, 120, 107, 113, 105, 80, 114
])

GEMINI_API_KEY = getattr(config, 'GEMINI_API_KEY', "AQ.Ab8RN6KDCvEgGaa-RBFKc1IX6TtvQaQ7aDee7q923av6EOLCbA")

class LingoLensApp(App):
    def build(self):
        self.src_lang = "ka"
        self.target_lang = "en"
        self.camera_active = False

        main_layout = BoxLayout(orientation='vertical', spacing=8, padding=10)

        # 1. Header (სათაური და მენიუს ღილაკი)
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
            text="⚙️ მენიუ",
            size_hint_x=0.3,
            background_color=(0.3, 0.3, 0.8, 1),
            on_press=self.open_menu_popup
        )
        
        header.add_widget(title_label)
        header.add_widget(btn_menu)
        main_layout.add_widget(header)

        # 2. ენის არჩევა და შეცვლა (Language Bar)
        lang_layout = BoxLayout(size_hint_y=0.08, spacing=5)
        self.btn_src = Button(text=f"A: {self.src_lang.upper()}", on_press=self.toggle_src_lang)
        self.btn_swap = Button(text="🔄 შეცვლა", background_color=(0.1, 0.4, 0.6, 1), on_press=self.swap_languages)
        self.btn_target = Button(text=f"B: {self.target_lang.upper()}", on_press=self.toggle_target_lang)
        
        lang_layout.add_widget(self.btn_src)
        lang_layout.add_widget(self.btn_swap)
        lang_layout.add_widget(self.btn_target)
        main_layout.add_widget(lang_layout)

        # 3. ორმხრივი დიალოგი (Live Dialogue Speaker Buttons)
        speaker_layout = BoxLayout(size_hint_y=0.15, spacing=8)
        self.btn_speaker_a = Button(
            text=f"🎙️ [{self.src_lang.upper()}] Speaker A\n(ცოცხალი დიალოგი)",
            background_color=(0.1, 0.6, 0.3, 1),
            halign='center',
            on_press=lambda x: self.start_live_dialogue("speaker_a")
        )
        self.btn_speaker_b = Button(
            text=f"🎙️ [{self.target_lang.upper()}] Speaker B\n(ცოცხალი დიალოგი)",
            background_color=(0.7, 0.2, 0.2, 1),
            halign='center',
            on_press=lambda x: self.start_live_dialogue("speaker_b")
        )
        speaker_layout.add_widget(self.btn_speaker_a)
        speaker_layout.add_widget(self.btn_speaker_b)
        main_layout.add_widget(speaker_layout)

        # 4. SMS / ტექსტის თარგმანის ველები
        self.input_text = TextInput(
            hint_text="ჩაწერეთ SMS, ტექსტი ან შეტყობინება...",
            size_hint_y=0.3,
            multiline=True
        )
        self.output_text = TextInput(
            hint_text="თარგმანი გამოჩნდება აქ...",
            size_hint_y=0.3,
            readonly=True,
            multiline=True
        )
        main_layout.add_widget(self.input_text)
        main_layout.add_widget(self.output_text)

        # Status Bar
        self.status_label = Label(text="სისტემა მზადაა", size_hint_y=0.04, color=(0.7, 0.7, 0.7, 1))
        main_layout.add_widget(self.status_label)

        return main_layout

    # --- მენიუს ფანჯარა (Popup) ---
    def open_menu_popup(self, instance):
        menu_content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        self.camera_box = BoxLayout(size_hint_y=0.4)
        self.camera_placeholder = Label(text="📷 კამერა გათიშულია.")
        self.camera_box.add_widget(self.camera_placeholder)
        menu_content.add_widget(self.camera_box)

        menu_grid = GridLayout(cols=2, spacing=8, size_hint_y=0.5)
        menu_grid.add_widget(Button(text="📷 კამერის ჩართვა", on_press=self.toggle_camera))
        menu_grid.add_widget(Button(text="🔍 Live OCR", on_press=self.run_ocr))
        menu_grid.add_widget(Button(text="🎓 Academic AI", on_press=self.academic_ai))
        menu_grid.add_widget(Button(text="📚 გრამატიკა", on_press=self.explain_grammar))
        menu_grid.add_widget(Button(text="🔊 წაკითხვა", on_press=self.read_text))
        menu_grid.add_widget(Button(text="📋 დაკოპირება", on_press=self.copy_text))
        menu_grid.add_widget(Button(text="📜 ისტორია", on_press=self.show_history))
        menu_grid.add_widget(Button(text="🗑️ გასუფთავება", on_press=self.clear_all))

        menu_content.add_widget(menu_grid)

        btn_close = Button(text="❌ მენიუს დახურვა", size_hint_y=0.1, background_color=(0.8, 0.2, 0.2, 1))
        menu_content.add_widget(btn_close)

        popup = Popup(
            title="დამატებითი ფუნქციები და პარამეტრები",
            content=menu_content,
            size_hint=(0.9, 0.85)
        )
        btn_close.bind(on_press=popup.dismiss)
        popup.open()

    # --- ენების გადართვა ---
    def update_speaker_labels(self):
        self.btn_src.text = f"A: {self.src_lang.upper()}"
        self.btn_target.text = f"B: {self.target_lang.upper()}"
        self.btn_speaker_a.text = f"🎙️ [{self.src_lang.upper()}] Speaker A\n(ცოცხალი დიალოგი)"
        self.btn_speaker_b.text = f"🎙️ [{self.target_lang.upper()}] Speaker B\n(ცოცხალი დიალოგი)"

    def swap_languages(self, instance):
        self.src_lang, self.target_lang = self.target_lang, self.src_lang
        self.update_speaker_labels()

    def toggle_src_lang(self, instance):
        self.src_lang = "en" if self.src_lang == "ka" else "ka"
        self.update_speaker_labels()

    def toggle_target_lang(self, instance):
        self.target_lang = "en" if self.target_lang == "ka" else "ka"
        self.update_speaker_labels()

    # --- API და თარგმნის ლოგიკა ---
    def start_live_dialogue(self, mode):
        from_l = self.src_lang if mode == "speaker_a" else self.target_lang
        to_l = self.target_lang if mode == "speaker_a" else self.src_lang

        text = self.input_text.text.strip()
        if not text:
            self.status_label.text = "⚠️ ჩაწერეთ ტექსტი ველში!"
            return

        # თუ offline_engine არსებობს და ინტერნეტი არ არის, იყენებს მას
        if offline_engine and hasattr(offline_engine, 'translate'):
            try:
                res = offline_engine.translate(text, from_l, to_l)
                if res:
                    self.output_text.text = res
                    self.status_label.text = "✅ ოფლაინ თარგმანი"
                    return
            except Exception:
                pass

        prompt = f"Translate dialogue from {from_l} to {to_l}: '{text}'"
        self.call_gemini_api(prompt)

    def call_gemini_api(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                translated_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                self.output_text.text = translated_text
                self.status_label.text = "✅ თარგმანი მზადაა"
            else:
                self.output_text.text = f"API Error: {response.status_code}"
        except Exception as e:
            self.output_text.text = f"ქსელის შეცდომა: {str(e)}"

    # --- მენიუს ფუნქციები ---
    def toggle_camera(self, instance):
        if not self.camera_active:
            try:
                self.camera_box.clear_widgets()
                self.camera_obj = Camera(play=True, resolution=(640, 480))
                self.camera_box.add_widget(self.camera_obj)
                self.camera_active = True
                self.status_label.text = "📷 კამერა ჩართულია"
            except Exception as e:
                self.status_label.text = f"კამერის შეცდომა: {str(e)}"
        else:
            self.camera_box.clear_widgets()
            self.camera_box.add_widget(self.camera_placeholder)
            self.camera_active = False
            self.status_label.text = "📷 კამერა გათიშულია"

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
        self.status_label.text = "გასუფთავებულია"

    def copy_text(self, instance):
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(self.output_text.text)
        self.status_label.text = "დაკოპირებულია!"

    def read_text(self, instance):
        self.status_label.text = "ტექსტის წაკითხვა..."

    def run_ocr(self, instance):
        self.status_label.text = "OCR პროცესი..."

    def show_history(self, instance):
        self.output_text.text = "ისტორია ცარიელია."

if __name__ == "__main__":
    LingoLensApp().run()
