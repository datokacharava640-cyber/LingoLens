import os
import json
import sqlite3
import requests
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup

# ==================== OPTIONAL DOCUMENT READERS ====================
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

FONT_PATH = "NotoSansGeorgian-Regular.ttf"
try:
    if os.path.exists(FONT_PATH):
        LabelBase.register(name="Roboto", fn_regular=FONT_PATH)
except Exception as e:
    print(f"Font Error: {e}")

try:
    from plyer import tts, filechooser
except Exception:
    tts = None
    filechooser = None

BUILTIN_GEMINI_KEY = "AQ.Ab8RN6JRsQmchpFvza1mUDtsUWVQNye3OmrJWcCOrmV5UuWqWQ"

KV_DESIGN = """
<Label>:
    font_name: "NotoSansGeorgian-Regular.ttf" if os.path.exists("NotoSansGeorgian-Regular.ttf") else "Roboto"

<TextInput>:
    font_name: "NotoSansGeorgian-Regular.ttf" if os.path.exists("NotoSansGeorgian-Regular.ttf") else "Roboto"

<Button>:
    font_name: "NotoSansGeorgian-Regular.ttf" if os.path.exists("NotoSansGeorgian-Regular.ttf") else "Roboto"

<RoundedButton>:
    background_color: (0, 0, 0, 0)
    background_normal: ''
    color: (1, 1, 1, 1)
    bold: True
    font_size: '12sp'
    canvas.before:
        Color:
            rgba: self.bg_color if hasattr(self, 'bg_color') else (0.18, 0.24, 0.35, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]
"""

Builder.load_string(KV_DESIGN)

class RoundedButton(Button):
    def __init__(self, bg_color=(0.18, 0.24, 0.35, 1), **kwargs):
        self.bg_color = bg_color
        super().__init__(**kwargs)

# ==================== SPLIT SCREEN DIALOGUE POPUP ====================
class SplitDialoguePopup(Popup):
    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.title = "🗣️ ორმხრივი დიალოგის რეჟიმი (Live Dialogue)"
        self.size_hint = (0.95, 0.9)
        self.api_key = api_key

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Person A (Top - Inverted visual feel)
        self.box_a = BoxLayout(orientation='vertical', spacing=5)
        self.box_a.add_widget(Label(text="[b]მოლაპარაკე A (ქართული)[/b]", markup=True, color=(0.4, 0.7, 1, 1)))
        self.label_a = Label(text="[ტექსტი A]", markup=True, color=(0.9, 0.9, 0.9, 1))
        self.box_a.add_widget(self.label_a)
        btn_speak_a = RoundedButton(text="🎙️ საუბარი A (ka)", bg_color=(0.2, 0.5, 0.8, 1), size_hint_y=0.4)
        btn_speak_a.bind(on_press=lambda x: self.start_stt("ka-GE", is_person_a=True))
        self.box_a.add_widget(btn_speak_a)

        # Divider
        layout.add_widget(self.box_a)
        layout.add_widget(Label(text="-----------------------------------", size_hint_y=0.05))

        # Person B (Bottom)
        self.box_b = BoxLayout(orientation='vertical', spacing=5)
        self.box_b.add_widget(Label(text="[b]მოლაპარაკე B (English)[/b]", markup=True, color=(0.4, 1, 0.6, 1)))
        self.label_b = Label(text="[Text B]", markup=True, color=(0.9, 0.9, 0.9, 1))
        self.box_b.add_widget(self.label_b)
        btn_speak_b = RoundedButton(text="🎙️ Speak B (en)", bg_color=(0.12, 0.6, 0.4, 1), size_hint_y=0.4)
        btn_speak_b.bind(on_press=lambda x: self.start_stt("en-US", is_person_a=False))
        self.box_b.add_widget(btn_speak_b)

        layout.add_widget(self.box_b)

        close_btn = RoundedButton(text="✖ დახურვა", bg_color=(0.8, 0.2, 0.2, 1), size_hint_y=0.15)
        close_btn.bind(on_press=self.dismiss)
        layout.add_widget(close_btn)

        self.content = layout

    def start_stt(self, lang_code, is_person_a=True):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)
                
                PythonActivity.mActivity.startActivityForResult(intent, 5002 if is_person_a else 5003)
            except Exception as e:
                print(f"STT Error: {e}")

# ==================== MAIN LAYOUT ====================
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
        self.api_key = BUILTIN_GEMINI_KEY
        self.src_lang = "ka"
        self.target_lang = "en"

        # Header
        self.add_widget(Label(text="[b]LingoLens Ultra Pro v5.0[/b]", markup=True, font_size='20sp', size_hint_y=0.06, color=(0.35, 0.65, 1, 1)))
        
        # Status Bar
        self.status_label = Label(text="⚡ Real-Time Multi-Format AI Engine", color=(0.25, 0.85, 0.5, 1), font_size='11sp', size_hint_y=0.03)
        self.add_widget(self.status_label)

        # Text Input
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი, ატვირთეთ PDF/DOCX ან გამოიყენეთ დიალოგი...", 
            multiline=True, 
            size_hint_y=0.3, 
            background_color=(0.08, 0.1, 0.15, 1), 
            foreground_color=(0.95, 0.95, 0.98, 1)
        )
        self.add_widget(self.text_input)

        # Output Text
        self.output_label = Label(
            text="[AI თარგმანი გამოჩნდება აქ]", 
            markup=True, 
            size_hint_y=0.3, 
            color=(0.8, 0.85, 0.92, 1)
        )
        self.add_widget(self.output_label)

        # Actions Bar
        actions = GridLayout(cols=3, spacing=6, size_hint_y=0.12)
        
        btn_trans = RoundedButton(text="✨ AI თარგმნა", bg_color=(0.12, 0.55, 0.38, 1))
        btn_trans.bind(on_press=lambda x: threading.Thread(target=self.translate_text, daemon=True).start())

        btn_dialogue = RoundedButton(text="🗣️ ცოცხალი დიალოგი\n(Split Screen)", bg_color=(0.55, 0.25, 0.6, 1))
        btn_dialogue.bind(on_press=lambda x: SplitDialoguePopup(self.api_key).open())

        btn_docs = RoundedButton(text="📁 PDF/DOCX/TXT\nატვირთვა", bg_color=(0.2, 0.45, 0.75, 1))
        btn_docs.bind(on_press=self.import_document_file)

        actions.add_widget(btn_trans)
        actions.add_widget(btn_dialogue)
        actions.add_widget(btn_docs)
        self.add_widget(actions)

    def translate_text(self):
        input_txt = self.text_input.text.strip()
        if not input_txt: return

        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '⏳ AI ინარჩუნებს ფორმატს და თარგმნის...'))
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        # Advanced layout retention prompt
        prompt = f"Translate accurately into target language '{self.target_lang}'. PRESERVE all original formatting, paragraphs, tables, and structures. Output ONLY translated text: {input_txt}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            res = requests.post(url, json=payload, timeout=12).json()
            translated = res['candidates'][0]['content']['parts'][0]['text'].strip()
            
            Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', translated))
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '✓ თარგმანი მზადაა (სტრუქტურა შენარჩუნებულია)'))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f'შეცდომა: {e}'))

    # Advanced Multi-Format Document Reader (PDF, DOCX, TXT)
    def import_document_file(self, instance):
        if filechooser:
            try:
                filechooser.open_file(on_selection=self.on_file_selected)
            except Exception as e:
                self.status_label.text = f"ფაილის შეცდომა: {e}"
        else:
            self.status_label.text = "File Picker მიუწვდომელია"

    def on_file_selected(self, selection):
        if not selection or not os.path.exists(selection[0]): return
        file_path = selection[0]
        ext = os.path.splitext(file_path)[1].lower()
        extracted_text = ""

        try:
            if ext == ".txt":
                with open(file_path, 'r', encoding='utf-8') as f:
                    extracted_text = f.read()
            elif ext == ".pdf" and PyPDF2:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        extracted_text += page.extract_text() + "\n"
            elif ext == ".docx" and docx:
                doc = docx.Document(file_path)
                extracted_text = "\n".join([p.text for p in doc.paragraphs])
            else:
                self.status_label.text = "არამხარდაჭერილი ფორმატი ან აკლია PyPDF2/python-docx"
                return

            self.text_input.text = extracted_text[:3000] # Limit first 3000 chars
            self.status_label.text = f"📄 წარმატებით ჩაიტვირთა: {os.path.basename(file_path)}"
        except Exception as e:
            self.status_label.text = f"დოკუმენტის წაკითხვის შეცდომა: {e}"

class LingoLensApp(App):
    def build(self):
        return MainLayout()

if __name__ == '__main__':
    LingoLensApp().run()
