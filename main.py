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
from kivy.clock import Clock
from kivy.utils import platform

# --- 1. Android-ის სისტემური ბიბლიოთეკების ინტეგრაცია ---
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.CAMERA,
        Permission.RECORD_AUDIO,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE
    ])
    try:
        from plyer import stt, tts, clipboard
    except Exception:
        stt = tts = clipboard = None
else:
    stt = tts = clipboard = None

# --- 2. პროექტის დამხმარე ფაილების იმპორტი ---
try:
    import config
except ImportError:
    config = None

try:
    import offline_engine
except ImportError:
    offline_engine = None

# --- 3. API Key და Endpoint-ის დეკოდირება ---
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

        # 1. Header (სათაური და მენიუ)
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

        # 2. ენის არჩევა და სვაპი
        lang_layout = BoxLayout(size_hint_y=0.08, spacing=5)
        self.btn_src = Button(text=f"A: {self.src_lang.upper()}", on_press=self.toggle_src_lang)
        self.btn_swap = Button(text="🔄 შეცვლა", background_color=(0.1, 0.4, 0.6, 1), on_press=self.swap_languages)
        self.btn_target = Button(text=f"B: {self.target_lang.upper()}", on_press=self.toggle_target_lang)
        
        lang_layout.add_widget(self.btn_src)
        lang_layout.add_widget(self.btn_swap)
        lang_layout.add_widget(self.btn_target)
        main_layout.add_widget(lang_layout)

        # 3. რეალური ორმხრივი ცოცხალი დიალოგი (ხმოვანი მოსმენით)
        speaker_layout = BoxLayout(size_hint_y=0.15, spacing=8)
        self.btn_speaker_a = Button(
            text=f"🎙️ [{self.src_lang.upper()}] Speaker A\n(დააჭირეთ ხმით საუბრისთვის)",
            background_color=(0.1, 0.6, 0.3, 1),
            halign='center',
            on_press=lambda x: self.start_voice_dialogue("speaker_a")
        )
        self.btn_speaker_b = Button(
            text=f"🎙️ [{self.target_lang.upper()}] Speaker B\n(დააჭირეთ ხმით საუბრისთვის)",
            background_color=(0.7, 0.2, 0.2, 1),
            halign='center',
            on_press=lambda x: self.start_voice_dialogue("speaker_b")
        )
        speaker_layout.add_widget(self.btn_speaker_a)
        speaker_layout.add_widget(self.btn_speaker_b)
        main_layout.add_widget(speaker_layout)

        # 4. SMS / ტექსტური თარგმანის ველები
        self.input_text = TextInput(
            hint_text="ჩაწერეთ SMS, ტექსტი ან ილაპარაკეთ ხმით...",
            size_hint_y=0.3,
            multiline=True
        )
        self.output_text = TextInput(
            hint_text="ნათარგმნი ტექსტი გამოჩნდება აქ...",
            size_hint_y=0.3,
            readonly=True,
            multiline=True
        )
        main_layout.add_widget(self.input_text)
        main_layout.add_widget(self.output_text)

        # Status Footer
        self.status_label = Label(text="სისტემა მზადაა", size_hint_y=0.04, color=(0.7, 0.7, 0.7, 1))
        main_layout.add_widget(self.status_label)

        return main_layout

    # --- მენიუს ფანჯარა (Popup) ---
    def open_menu_popup(self, instance):
        menu_content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # კამერის ზონა
        self.camera_box = BoxLayout(size_hint_y=0.4)
        self.camera_placeholder = Label(text="📷 კამერა გათიშულია.")
        self.camera_box.add_widget(self.camera_placeholder)
        menu_content.add_widget(self.camera_box)

        # ფუნქციების ბადე
        menu_grid = GridLayout(cols=2, spacing=8, size_hint_y=0.5)
        menu_grid.add_widget(Button(text="📷 კამერის ჩართვა", on_press=self.toggle_camera))
        menu_grid.add_widget(Button(text="🔍 Live OCR (ტექსტის ამოცნობა)", on_press=self.run_ocr))
        menu_grid.add_widget(Button(text="🎓 Academic AI", on_press=self.academic_ai))
        menu_grid.add_widget(Button(text="📚 გრამატიკა", on_press=self.explain_grammar))
        menu_grid.add_widget(Button(text="🔊 წაკითხვა (TTS)", on_press=self.read_text))
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
        self.btn_speaker_a.text = f"🎙️ [{self.src_lang.upper()}] Speaker A\n(ხმოვანი საუბარი)"
        self.btn_speaker_b.text = f"🎙️ [{self.target_lang.upper()}] Speaker B\n(ხმოვანი საუბარი)"

    def swap_languages(self, instance):
        self.src_lang, self.target_lang = self.target_lang, self.src_lang
        self.update_speaker_labels()

    def toggle_src_lang(self, instance):
        self.src_lang = "en" if self.src_lang == "ka" else "ka"
        self.update_speaker_labels()

    def toggle_target_lang(self, instance):
        self.target_lang = "en" if self.target_lang == "ka" else "ka"
        self.update_speaker_labels()

    # --- 🎙️ 1. რეალური ხმოვანი ამოცნობა (Speech to Text) ---
    def start_voice_dialogue(self, mode):
        from_l = self.src_lang if mode == "speaker_a" else self.target_lang
        to_l = self.target_lang if mode == "speaker_a" else self.src_lang

        if stt and platform == 'android':
            try:
                self.status_label.text = f"🎙️ გისმენთ ({from_l.upper()})..."
                stt.start()
                # მოსმენის შედეგის დამუშავება
                Clock.schedule_once(lambda dt: self.check_stt_result(from_l, to_l), 4)
            except Exception as e:
                self.status_label.text = f"STT შეცდომა: {str(e)}"
        else:
            # თუ ხმოვანი შეყვანა მიუწვდომელია, იყენებს ჩაწერილ ტექსტს
            text = self.input_text.text.strip()
            if text:
                self.translate_dialogue(text, from_l, to_l)
            else:
                self.status_label.text = "⚠️ შეიყვანეთ ტექსტი ან ჩართეთ მიკროფონი!"

    def check_stt_result(self, from_l, to_l):
        if stt and hasattr(stt, 'results') and stt.results:
            spoken_text = stt.results[0]
            self.input_text.text = spoken_text
            self.translate_dialogue(spoken_text, from_l, to_l)

    def translate_dialogue(self, text, from_l, to_l):
        prompt = f"Real-time dialogue translation from {from_l} to {to_l}: '{text}'"
        self.call_gemini_api(prompt, auto_speak=True)

    # --- 🌐 Gemini API მოთხოვნა ---
    def call_gemini_api(self, prompt, auto_speak=False):
        # ოფლაინ შემოწმება
        if offline_engine and hasattr(offline_engine, 'translate'):
            try:
                res = offline_engine.translate(prompt, self.src_lang, self.target_lang)
                if res:
                    self.output_text.text = res
                    self.status_label.text = "✅ ოფლაინ თარგმანი"
                    if auto_speak:
                        self.read_text(None)
                    return
            except Exception:
                pass

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        def make_request():
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    res_data = response.json()
                    translated_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                    Clock.schedule_once(lambda dt: self.update_output(translated_text, auto_speak))
                else:
                    Clock.schedule_once(lambda dt: self.update_output(f"API Error: {response.status_code}", False))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.update_output(f"ქსელის შეცდომა: {str(e)}", False))

        threading.Thread(target=make_request).start()

    def update_output(self, text, auto_speak):
        self.output_text.text = text
        self.status_label.text = "✅ თარგმანი მზადაა"
        if auto_speak:
            self.read_text(None)

    # --- 🔊 2. რეალური გახმოვანება (Text to Speech) ---
    def read_text(self, instance):
        text_to_read = self.output_text.text.strip()
        if text_to_read:
            if tts and platform == 'android':
                try:
                    tts.speak(text_to_read)
                    self.status_label.text = "🔊 მიმდინარეობს გახმოვანება..."
                except Exception as e:
                    self.status_label.text = f"TTS შეცდომა: {str(e)}"
            else:
                self.status_label.text = "🔊 გახმოვანება მიუწვდომელია მოწყობილობაზე."

    # --- 🔍 3. რეალური Live OCR (კამერიდან ტექსტის ამოცნობა) ---
    def run_ocr(self, instance):
        if self.camera_active and self.camera_obj:
            try:
                # კამერის კადრის შენახვა
                photo_path = os.path.join(self.user_data_dir, "ocr_frame.png")
                self.camera_obj.export_to_png(photo_path)
                self.status_label.text = "🔍 სურათი გადაღებულია, მიმდინარეობს OCR..."

                # Gemini Vision API-ის გამოძახება სურათის ტექსტის ამოსაცნობად
                threading.Thread(target=self.process_ocr_image, args=(photo_path,)).start()
            except Exception as e:
                self.status_label.text = f"OCR შეცდომა: {str(e)}"
        else:
            self.status_label.text = "⚠️ ჩართეთ კამერა მენიუდან!"

    def process_ocr_image(self, photo_path):
        import base64
        try:
            with open(photo_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Extract all readable text from this image accurately and translate it to Georgian/English."},
                        {"inline_data": {"mime_type": "image/png", "data": encoded_string}}
                    ]
                }]
            }
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                res_data = response.json()
                extracted_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                Clock.schedule_once(lambda dt: self.update_ocr_result(extracted_text))
            else:
                Clock.schedule_once(lambda dt: self.update_status(f"OCR API Error: {response.status_code}"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f"OCR Error: {str(e)}"))

    def update_ocr_result(self, text):
        self.output_text.text = text
        self.status_label.text = "✅ ტექსტი წარმატებით ამოიცნო!"

    def update_status(self, status):
        self.status_label.text = status

    # --- კამერის მართვა ---
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

    # --- დამხმარე ფუნქციები ---
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
        if self.output_text.text:
            if clipboard and platform == 'android':
                clipboard.copy(self.output_text.text)
            else:
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(self.output_text.text)
            self.status_label.text = "დაკოპირებულია!"

    def show_history(self, instance):
        self.output_text.text = "ისტორია ცარიელია."

if __name__ == "__main__":
    LingoLensApp().run()
