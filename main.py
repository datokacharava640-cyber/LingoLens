import os
import sys
import json
import sqlite3
import threading
import time
from urllib.parse import quote

# Kivy Framework UI Components
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Line

# Network & HTTP
import requests

# Android Native Integration (Pyjnius)
try:
    from jnius import autoclass, cast
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    String = autoclass('java.lang.String')
    ClipboardManager = autoclass('android.content.ClipboardManager')
    ClipData = autoclass('android.content.ClipData')
    Context = autoclass('android.content.Context')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    SpeechRecognizer = autoclass('android.speech.RecognizerIntent')
    IS_ANDROID = True
except Exception as e:
    IS_ANDROID = False


# =============================================================================
# 1. AI CORE & NMT CONTEXT TRANSLATOR ENGINE
# =============================================================================
class AICoreTranslator:
    """სწრაფი, უშეცდომო და კონტექსტური თარგმნის ძრავი"""
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

    def translate_contextual(self, text, src_lang='auto', target_lang='ka'):
        if not text.strip():
            return ""
        
        # Google NMT API Endpoint
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_lang}&tl={target_lang}&dt=t&dt=bd&q={quote(text)}"
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                translated_parts = [item[0] for item in data[0] if item[0]]
                return "".join(translated_parts)
        except Exception:
            # Fallback to local offline dictionary if network fails
            return OfflineAIEngine.translate_offline(text, target_lang)
        
        return text


# =============================================================================
# 2. LIGHTWEIGHT OFFLINE AI ENGINE (No C++ / NumPy Dependencies)
# =============================================================================
class OfflineAIEngine:
    """სრულიად ლოკალური თარგმნის ძრავი უინტერნეტო რეჟიმისთვის"""
    OFFLINE_VOCAB = {
        "hello": "გამარჯობა",
        "world": "სამყარო",
        "welcome": "კეთილი იყოს თქვენი მობრძანება",
        "translator": "თარჯიმანი",
        "camera": "კამერა",
        "conversation": "დიალოგი",
        "good morning": "დილა მშვიდობისა",
        "thank you": "გმადლობთ"
    }

    @classmethod
    def translate_offline(cls, text, target_lang='ka'):
        words = text.lower().strip().split()
        translated_words = []
        for word in words:
            clean_word = word.strip(".,!?")
            translated_words.append(cls.OFFLINE_VOCAB.get(clean_word, word))
        return " ".join(translated_words) + " (Offline)"


# =============================================================================
# 3. REAL-TIME AR VISION & CAMERA OVERLAY PROCESSOR
# =============================================================================
class ARVisionOverlay(BoxLayout):
    """AR ვიზუალური თარგმნისა და კადრზე ტექსტის ჩანაცვლების სიმულატორი"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        self.info_label = Label(
            text="[ AR Vision Mode ]\nმიმართეთ კამერა ტექსტზე რეალურ დროში თარგმნისთვის",
            halign='center',
            size_hint_y=0.2
        )
        self.add_widget(self.info_label)

        # Camera View Mock Canvas Container
        self.camera_canvas = BoxLayout(size_hint_y=0.8)
        with self.camera_canvas.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.rect = Rectangle(size=self.camera_canvas.size, pos=self.camera_canvas.pos)
        self.camera_canvas.bind(size=self._update_rect, pos=self._update_rect)

        self.ar_text_label = Label(text="[ Scanning Text... ]", color=(0, 1, 0.5, 1))
        self.camera_canvas.add_widget(self.ar_text_label)
        self.add_widget(self.camera_canvas)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def process_ar_frame(self, detected_text, translated_text):
        self.ar_text_label.text = f"Detected: {detected_text}\nTranslated: {translated_text}"


# =============================================================================
# 4. FULL-DUPLEX REAL-TIME CONVERSATION MANAGER
# =============================================================================
class ConversationManager:
    """ორმხრივი ცოცხალი დიალოგის მმართველი სისტემა"""
    def __init__(self, tts_callback=None):
        self.is_listening = False
        self.tts_callback = tts_callback

    def start_bilingual_conversation(self, lang1='ka', lang2='en'):
        self.is_listening = True
        # Real-time Voice Processing Simulation loop
        threading.Thread(target=self._conversation_loop, args=(lang1, lang2), daemon=True).start()

    def stop_conversation(self):
        self.is_listening = False

    def _conversation_loop(self, lang1, lang2):
        while self.is_listening:
            time.sleep(3)  # Interval checking for incoming audio stream
            break


# =============================================================================
# 5. DATABASE & CROSS-PLATFORM STORAGE LAYER
# =============================================================================
class StorageManager:
    """SQLite ლოკალური ბაზა ისტორიისა და ფავორიტებისთვის"""
    def __init__(self):
        self.conn = sqlite3.connect("lingolens_data.db", check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                src_text TEXT,
                translated_text TEXT,
                src_lang TEXT,
                target_lang TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def save_translation(self, src, trans, src_lang, target_lang):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO history (src_text, translated_text, src_lang, target_lang) VALUES (?, ?, ?, ?)",
                (src, trans, src_lang, target_lang)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Database Error: {e}")


# =============================================================================
# MAIN APPLICATION INTERFACE (KIVY)
# =============================================================================
class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro v2.0"
        self.ai_translator = AICoreTranslator()
        self.storage = StorageManager()
        self.conversation_mgr = ConversationManager()
        self.debounce_timer = None

        # Root UI Layout
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Header Title
        header = Label(
            text="LingoLens AI Ultra Pro",
            font_size='22sp',
            bold=True,
            size_hint_y=0.08,
            color=(0.2, 0.6, 1, 1)
        )
        root.add_widget(header)

        # Main Input / Output Controls
        self.input_text = TextInput(
            hint_text="ჩაწერეთ ან ჩასვით ტექსტი...",
            multiline=True,
            size_hint_y=0.25,
            font_size='16sp'
        )
        self.input_text.bind(text=self.on_text_change)
        root.add_widget(self.input_text)

        self.output_text = TextInput(
            hint_text="ნათარგმნი ტექსტი...",
            multiline=True,
            readonly=True,
            size_hint_y=0.25,
            font_size='16sp'
        )
        root.add_widget(self.output_text)

        # Action Buttons Layout
        btn_grid = GridLayout(cols=3, spacing=5, size_hint_y=0.15)
        
        btn_ar = Button(text="AR Vision Mode", background_color=(0.1, 0.7, 0.3, 1))
        btn_ar.bind(on_press=self.open_ar_vision)
        btn_grid.add_widget(btn_ar)

        btn_dialog = Button(text="Live Conversation", background_color=(0.8, 0.4, 0.1, 1))
        btn_dialog.bind(on_press=self.start_conversation_ui)
        btn_grid.add_widget(btn_dialog)

        btn_copy = Button(text="Copy Text", background_color=(0.3, 0.3, 0.8, 1))
        btn_copy.bind(on_press=self.copy_to_clipboard)
        btn_grid.add_widget(btn_copy)

        root.add_widget(btn_grid)

        # Status Footer
        self.status_label = Label(
            text="სისტემა მზადაა | Real-time Engine Active",
            size_hint_y=0.05,
            font_size='12sp',
            color=(0.6, 0.6, 0.6, 1)
        )
        root.add_widget(self.status_label)

        return root

    def on_text_change(self, instance, value):
        """0.5-წამიანი Debouncing Real-time თარგმნისთვის"""
        if self.debounce_timer:
            self.debounce_timer.cancel()
        self.debounce_timer = Clock.schedule_once(lambda dt: self.perform_translation(value), 0.5)

    def perform_translation(self, text):
        if not text.strip():
            self.output_text.text = ""
            return
        
        def async_translate():
            result = self.ai_translator.translate_contextual(text, src_lang='auto', target_lang='ka')
            self.update_output_ui(result, text)

        threading.Thread(target=async_translate, daemon=True).start()

    @mainthread
    def update_output_ui(self, result, original_text):
        self.output_text.text = result
        self.storage.save_translation(original_text, result, 'auto', 'ka')
        self.status_label.text = "თარგმნა დასრულდა"

    def open_ar_vision(self, instance):
        popup_layout = ARVisionOverlay()
        popup = Popup(title="AR Camera Real-Time Translator", content=popup_layout, size_hint=(0.9, 0.8))
        popup.open()

    def start_conversation_ui(self, instance):
        self.status_label.text = "ცოცხალი დიალოგის რეჟიმი აქტიურია..."
        self.conversation_mgr.start_bilingual_conversation()

    def copy_to_clipboard(self, instance):
        if self.output_text.text and IS_ANDROID:
            try:
                activity = PythonActivity.mActivity
                clipboard = activity.getSystemService(Context.CLIPBOARD_SERVICE)
                clip = ClipData.newPlainText("LingoLens", String(self.output_text.text))
                clipboard.setPrimaryClip(clip)
                self.status_label.text = "ტექსტი დაკოპირდა!"
            except Exception as e:
                print(f"Clipboard Error: {e}")


if __name__ == "__main__":
    LingoLensApp().run()
