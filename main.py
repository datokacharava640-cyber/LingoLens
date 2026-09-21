import os
import requests
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.graphics import PushMatrix, PopMatrix, Rotate

# --- 1. Android სისტემური ნებართვები ---
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.CAMERA,
        Permission.RECORD_AUDIO,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE
    ])
    try:
        from plyer import stt, tts, clipboard, share
    except Exception:
        stt = tts = clipboard = share = None
else:
    stt = tts = clipboard = share = None

# --- 2. შრიფტის ჩატვირთვა ---
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None

# --- 3. ენების მსოფლიო ჩამონათვალი ---
LANGUAGES = {
    "KA": "ka", "EN": "en", "DE": "de", "FR": "fr", "ES": "es",
    "IT": "it", "RU": "ru", "TR": "tr", "ZH": "zh-CN", "JA": "ja",
    "AR": "ar", "UK": "uk", "PL": "pl", "EL": "el", "HE": "he"
}
LANG_NAMES = list(LANGUAGES.keys())

try:
    import config
except ImportError:
    config = None

GEMINI_API_KEY = getattr(config, 'GEMINI_API_KEY', "")


class LingoLensApp(App):
    def build(self):
        self.src_lang = "ka"
        self.target_lang = "en"
        self.camera_active = False

        main_layout = BoxLayout(orientation='vertical', spacing=6, padding=8)

        # 1. Header (სათაური და მენიუ)
        header = BoxLayout(size_hint_y=0.08, spacing=5)
        title_label = Label(
            text="LingoLens AI",
            font_size='20sp',
            color=(0, 1, 0, 1),
            bold=True,
            font_name=FONT_PATH,
            halign='left',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))
        
        btn_menu = Button(
            text="⚙️ მენიუ",
            size_hint_x=0.35,
            background_color=(0.3, 0.3, 0.8, 1),
            font_name=FONT_PATH,
            on_press=self.open_menu_popup
        )
        
        header.add_widget(title_label)
        header.add_widget(btn_menu)
        main_layout.add_widget(header)

        # 2. ენების არჩევის ჩამონათვალი (Dropdown / Spinner)
        lang_layout = BoxLayout(size_hint_y=0.08, spacing=5)
        
        self.spin_src = Spinner(
            text="KA",
            values=LANG_NAMES,
            size_hint_x=0.35,
            font_name=FONT_PATH
        )
        self.spin_src.bind(text=self.on_src_change)

        btn_swap = Button(
            text="🔄", 
            size_hint_x=0.15, 
            background_color=(0.1, 0.4, 0.6, 1), 
            font_name=FONT_PATH, 
            on_press=self.swap_languages
        )

        self.spin_target = Spinner(
            text="EN",
            values=LANG_NAMES,
            size_hint_x=0.35,
            font_name=FONT_PATH
        )
        self.spin_target.bind(text=self.on_target_change)

        lang_layout.add_widget(self.spin_src)
        lang_layout.add_widget(btn_swap)
        lang_layout.add_widget(self.spin_target)
        main_layout.add_widget(lang_layout)

        # 3. ხმოვანი დიალოგის ღილაკები
        speaker_layout = BoxLayout(size_hint_y=0.10, spacing=8)
        self.btn_speaker_a = Button(
            text=f"🎙️ [{self.src_lang.upper()}] Speaker A",
            background_color=(0.1, 0.6, 0.3, 1),
            font_name=FONT_PATH,
            on_press=lambda x: self.start_voice_dialogue("speaker_a")
        )
        self.btn_speaker_b = Button(
            text=f"🎙️ [{self.target_lang.upper()}] Speaker B",
            background_color=(0.7, 0.2, 0.2, 1),
            font_name=FONT_PATH,
            on_press=lambda x: self.start_voice_dialogue("speaker_b")
        )
        speaker_layout.add_widget(self.btn_speaker_a)
        speaker_layout.add_widget(self.btn_speaker_b)
        main_layout.add_widget(speaker_layout)

        # 4. ზონა 1: შეყვანილი ტექსტი
        main_layout.add_widget(Label(text="შეყვანილი ტექსტი / SMS (1):", size_hint_y=0.04, font_name=FONT_PATH, halign='left'))
        self.input_text = TextInput(
            hint_text="ჩაწერეთ ტექსტი თარგმნისთვის...",
            size_hint_y=0.20,
            multiline=True,
            font_name=FONT_PATH
        )
        self.input_text.bind(text=self.on_input_text_change)
        main_layout.add_widget(self.input_text)

        action_bar_1 = BoxLayout(size_hint_y=0.07, spacing=5)
        btn_listen_1 = Button(text="🔊 მოსმენა", font_name=FONT_PATH, background_color=(0.2, 0.6, 0.8, 1), on_press=lambda x: self.speak_text(self.input_text.text, self.src_lang))
        btn_copy_1 = Button(text="📋 დაკოპირება", font_name=FONT_PATH, on_press=lambda x: self.copy_to_clipboard(self.input_text.text))
        btn_share_1 = Button(text="📲 გაზიარება", font_name=FONT_PATH, background_color=(0.8, 0.5, 0.2, 1), on_press=lambda x: self.share_text(self.input_text.text))
        action_bar_1.add_widget(btn_listen_1)
        action_bar_1.add_widget(btn_copy_1)
        action_bar_1.add_widget(btn_share_1)
        main_layout.add_widget(action_bar_1)

        # 5. ზონა 2: თარგმანი
        main_layout.add_widget(Label(text="თარგმანი (2):", size_hint_y=0.04, font_name=FONT_PATH, halign='left'))
        self.output_text = TextInput(
            hint_text="ნათარგმნი ტექსტი გამოჩნდება აქ...",
            size_hint_y=0.20,
            readonly=True,
            multiline=True,
            font_name=FONT_PATH
        )
        main_layout.add_widget(self.output_text)

        action_bar_2 = BoxLayout(size_hint_y=0.07, spacing=5)
        btn_listen_2 = Button(text="🔊 მოსმენა", font_name=FONT_PATH, background_color=(0.2, 0.7, 0.3, 1), on_press=lambda x: self.speak_text(self.output_text.text, self.target_lang))
        btn_copy_2 = Button(text="📋 დაკოპირება", font_name=FONT_PATH, on_press=lambda x: self.copy_to_clipboard(self.output_text.text))
        btn_share_2 = Button(text="📲 გაზიარება", font_name=FONT_PATH, background_color=(0.8, 0.5, 0.2, 1), on_press=lambda x: self.share_text(self.output_text.text))
        action_bar_2.add_widget(btn_listen_2)
        action_bar_2.add_widget(btn_copy_2)
        action_bar_2.add_widget(btn_share_2)
        main_layout.add_widget(action_bar_2)

        self.status_label = Label(text="სისტემა მზადაა", size_hint_y=0.04, font_name=FONT_PATH, color=(0.7, 0.7, 0.7, 1))
        main_layout.add_widget(self.status_label)

        return main_layout

    # --- ენების არჩევა ---
    def on_src_change(self, spinner, text):
        self.src_lang = LANGUAGES.get(text, "ka")
        self.btn_speaker_a.text = f"🎙️ [{text}] Speaker A"

    def on_target_change(self, spinner, text):
        self.target_lang = LANGUAGES.get(text, "en")
        self.btn_speaker_b.text = f"🎙️ [{text}] Speaker B"

    def swap_languages(self, instance):
        src_curr = self.spin_src.text
        target_curr = self.spin_target.text
        self.spin_src.text = target_curr
        self.spin_target.text = src_curr

    # --- ავტომატური თარგმანი ტექსტის აკრეფისას ---
    def on_input_text_change(self, instance, value):
        if hasattr(self, '_debounce_timer') and self._debounce_timer:
            self._debounce_timer.cancel()
        if value.strip():
            self._debounce_timer = Clock.schedule_once(lambda dt: self.call_gemini_api(f"Translate from {self.src_lang} to {self.target_lang}: {value}"), 0.8)

    # --- 🌐 თარგმნის ფუნქცია (Fallback გარანტიით) ---
    def call_gemini_api(self, prompt, auto_speak=False):
        self.status_label.text = "🔄 მიმდინარეობს თარგმნა..."

        def make_request():
            translated_text = None
            raw_text = self.input_text.text.strip()
            
            if GEMINI_API_KEY:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                    headers = {"Content-Type": "application/json"}
                    payload = {"contents": [{"parts": [{"text": prompt}]}]}
                    response = requests.post(url, json=payload, headers=headers, timeout=6)
                    if response.status_code == 200:
                        res_data = response.json()
                        translated_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                except Exception:
                    pass

            # სარეზერვო თარგმანი Google Translate API-ით
            if not translated_text and raw_text:
                try:
                    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={self.src_lang}&tl={self.target_lang}&dt=t&q={requests.utils.quote(raw_text)}"
                    res = requests.get(url, timeout=5)
                    if res.status_code == 200:
                        translated_text = res.json()[0][0][0]
                except Exception as e:
                    translated_text = f"შეცდომა: {str(e)}"

            Clock.schedule_once(lambda dt: self.update_output(translated_text, auto_speak))

        threading.Thread(target=make_request).start()

    def update_output(self, text, auto_speak):
        if text:
            self.output_text.text = text
            self.status_label.text = "✅ თარგმანი მზადაა"
            if auto_speak:
                self.speak_text(text, self.target_lang)

    # --- 🔊 გახმოვანება (ქართული ენის სრული მხარდაჭერით) ---
    def speak_text(self, text, lang):
        if not text.strip():
            self.status_label.text = "⚠️ ტექსტი ცარიელია!"
            return

        self.status_label.text = f"🔊 გახმოვანება ({lang.upper()})..."

        def run_tts():
            try:
                # ქართული ენის ზუსტი კოდი Google TTS სერვერისთვის
                tts_lang = "ka" if lang == "ka" else lang
                url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={requests.utils.quote(text)}&tl={tts_lang}&client=tw-ob"
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get(url, headers=headers, timeout=7)
                if res.status_code == 200:
                    temp_file = os.path.join(self.user_data_dir, "temp_audio.mp3") if hasattr(self, 'user_data_dir') else "temp_audio.mp3"
                    with open(temp_file, "wb") as f:
                        f.write(res.content)
                    from kivy.core.audio import SoundLoader
                    sound = SoundLoader.load(temp_file)
                    if sound:
                        sound.play()
            except Exception as e:
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f"TTS შეცდომა: {str(e)}"))

        threading.Thread(target=run_tts).start()

    # --- 📷 კამერის ჩართვა (90°-ით სწორად დატრიალებით) ---
    def toggle_camera(self, instance):
        if not self.camera_active:
            try:
                self.camera_box.clear_widgets()
                self.camera_obj = Camera(play=True, resolution=(640, 480))
                
                # კამერის ვიზუალური დატრიალება Canvas-ით
                with self.camera_box.canvas.before:
                    PushMatrix()
                    Rotate(angle=-90, origin=self.camera_box.center)
                with self.camera_box.canvas.after:
                    PopMatrix()

                self.camera_box.add_widget(self.camera_obj)
                self.camera_active = True
                self.status_label.text = "📷 კამერა ჩართულია"
            except Exception as e:
                self.status_label.text = f"კამერის შეცდომა: {str(e)}"
        else:
            if hasattr(self, 'camera_obj') and self.camera_obj:
                self.camera_obj.play = False
            self.camera_box.clear_widgets()
            self.camera_box.add_widget(self.camera_placeholder)
            self.camera_active = False
            self.status_label.text = "📷 კამერა გათიშულია"

    # --- ⚙️ მენიუ ---
    def open_menu_popup(self, instance):
        menu_content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        self.camera_box = BoxLayout(size_hint_y=0.45)
        self.camera_placeholder = Label(text="📷 კამერა გათიშულია.", font_name=FONT_PATH)
        self.camera_box.add_widget(self.camera_placeholder)
        menu_content.add_widget(self.camera_box)

        menu_grid = GridLayout(cols=2, spacing=8, size_hint_y=0.45)
        menu_grid.add_widget(Button(text="📷 კამერის ჩართვა", font_name=FONT_PATH, on_press=self.toggle_camera))
        menu_grid.add_widget(Button(text="🔍 Live OCR (ტექსტი)", font_name=FONT_PATH, on_press=self.run_ocr))
        menu_grid.add_widget(Button(text="🎓 Academic AI", font_name=FONT_PATH, on_press=self.academic_ai))
        menu_grid.add_widget(Button(text="📚 გრამატიკა", font_name=FONT_PATH, on_press=self.explain_grammar))
        menu_grid.add_widget(Button(text="📜 ისტორია", font_name=FONT_PATH, on_press=self.show_history))
        menu_grid.add_widget(Button(text="🗑️ გასუფთავება", font_name=FONT_PATH, on_press=self.clear_all))

        menu_content.add_widget(menu_grid)

        btn_close = Button(text="❌ მენიუს დახურვა", font_name=FONT_PATH, size_hint_y=0.1, background_color=(0.8, 0.2, 0.2, 1))
        menu_content.add_widget(btn_close)

        popup = Popup(
            title="დამატებითი პარამეტრები",
            title_font=FONT_PATH,
            content=menu_content,
            size_hint=(0.95, 0.88)
        )
        btn_close.bind(on_press=popup.dismiss)
        popup.open()

    # --- 📲 გაზიარება და კოპირება ---
    def share_text(self, text):
        if text.strip():
            Clipboard.copy(text)
            self.status_label.text = "📋 ტექსტი დაკოპირდა!"

    def copy_to_clipboard(self, text):
        if text.strip():
            Clipboard.copy(text)
            self.status_label.text = "📋 ტექსტი დაკოპირდა!"

    # --- 🎙️ ხმოვანი დიალოგი ---
    def start_voice_dialogue(self, mode):
        from_l = self.src_lang if mode == "speaker_a" else self.target_lang
        to_l = self.target_lang if mode == "speaker_a" else self.src_lang

        if stt and platform == 'android':
            try:
                self.status_label.text = f"🎙️ გისმენთ ({from_l.upper()})..."
                stt.start()
                Clock.schedule_once(lambda dt: self.check_stt_result(from_l, to_l), 4)
            except Exception as e:
                self.status_label.text = f"STT შეცდომა: {str(e)}"
        else:
            text = self.input_text.text.strip()
            if text:
                self.call_gemini_api(f"Translate from {from_l} to {to_l}: {text}", auto_speak=True)

    def check_stt_result(self, from_l, to_l):
        if stt and hasattr(stt, 'results') and stt.results:
            spoken_text = stt.results[0]
            self.input_text.text = spoken_text
            self.call_gemini_api(f"Translate from {from_l} to {to_l}: {spoken_text}", auto_speak=True)

    # --- 🔍 OCR ---
    def run_ocr(self, instance):
        if self.camera_active and hasattr(self, 'camera_obj') and self.camera_obj:
            try:
                photo_path = os.path.join(self.user_data_dir, "ocr_frame.png") if hasattr(self, 'user_data_dir') else "ocr_frame.png"
                self.camera_obj.export_to_png(photo_path)
                self.status_label.text = "🔍 სურათი გადაღებულია..."
            except Exception as e:
                self.status_label.text = f"OCR შეცდომა: {str(e)}"

    def academic_ai(self, instance):
        if self.input_text.text.strip():
            self.call_gemini_api(f"Rewrite in formal academic tone: {self.input_text.text}")

    def explain_grammar(self, instance):
        if self.input_text.text.strip():
            self.call_gemini_api(f"Explain grammar step-by-step: {self.input_text.text}")

    def clear_all(self, instance):
        self.input_text.text = ""
        self.output_text.text = ""
        self.status_label.text = "გასუფთავებულია"

    def show_history(self, instance):
        self.output_text.text = "ისტორია ცარიელია."

if __name__ == "__main__":
    LingoLensApp().run()
