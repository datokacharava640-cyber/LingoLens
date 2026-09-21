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
from kivy.core.clipboard import Clipboard

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
        from plyer import stt, tts, clipboard, share
    except Exception:
        stt = tts = clipboard = share = None
else:
    stt = tts = clipboard = share = None

# --- 2. შრიფტის ჩატვირთვა ([X] სიმბოლოების თავიდან ასაცილებლად) ---
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None

# --- 3. API KEY (ჩასვი შენი მოქმედი API KEY) ---
GEMINI_API_KEY = "შენი_ახალი_GEMINI_API_KEY"


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

        # 2. ენის არჩევა და სვაპი
        lang_layout = BoxLayout(size_hint_y=0.08, spacing=5)
        self.btn_src = Button(text=f"A: {self.src_lang.upper()}", font_name=FONT_PATH, on_press=self.toggle_src_lang)
        self.btn_swap = Button(text="🔄 შეცვლა", background_color=(0.1, 0.4, 0.6, 1), font_name=FONT_PATH, on_press=self.swap_languages)
        self.btn_target = Button(text=f"B: {self.target_lang.upper()}", font_name=FONT_PATH, on_press=self.toggle_target_lang)
        
        lang_layout.add_widget(self.btn_src)
        lang_layout.add_widget(self.btn_swap)
        lang_layout.add_widget(self.btn_target)
        main_layout.add_widget(lang_layout)

        # 3. ცოცხალი ხმოვანი დიალოგის ღილაკები
        speaker_layout = BoxLayout(size_hint_y=0.12, spacing=8)
        self.btn_speaker_a = Button(
            text=f"🎙️ [{self.src_lang.upper()}] Speaker A\n(ხმოვანი საუბარი)",
            background_color=(0.1, 0.6, 0.3, 1),
            font_name=FONT_PATH,
            halign='center',
            on_press=lambda x: self.start_voice_dialogue("speaker_a")
        )
        self.btn_speaker_b = Button(
            text=f"🎙️ [{self.target_lang.upper()}] Speaker B\n(ხმოვანი საუბარი)",
            background_color=(0.7, 0.2, 0.2, 1),
            font_name=FONT_PATH,
            halign='center',
            on_press=lambda x: self.start_voice_dialogue("speaker_b")
        )
        speaker_layout.add_widget(self.btn_speaker_a)
        speaker_layout.add_widget(self.btn_speaker_b)
        main_layout.add_widget(speaker_layout)

        # --- 4. ზონა 1: შეყვანილი SMS / ტექსტი ---
        main_layout.add_widget(Label(text="შეყვანილი ტექსტი / SMS (1):", size_hint_y=0.04, font_name=FONT_PATH, halign='left'))
        self.input_text = TextInput(
            hint_text="ჩაწერეთ SMS, ტექსტი ან ილაპარაკეთ ხმით...",
            size_hint_y=0.22,
            multiline=True,
            font_name=FONT_PATH
        )
        main_layout.add_widget(self.input_text)

        # ზონა 1-ის მოქმედებები
        action_bar_1 = BoxLayout(size_hint_y=0.07, spacing=5)
        btn_listen_1 = Button(
            text="🔊 მოსმენა", 
            font_name=FONT_PATH,
            background_color=(0.2, 0.6, 0.8, 1),
            on_press=lambda x: self.speak_text(self.input_text.text, self.src_lang)
        )
        btn_copy_1 = Button(
            text="📋 დაკოპირება", 
            font_name=FONT_PATH,
            on_press=lambda x: self.copy_to_clipboard(self.input_text.text)
        )
        btn_share_1 = Button(
            text="📲 გაზიარება", 
            font_name=FONT_PATH,
            background_color=(0.8, 0.5, 0.2, 1),
            on_press=lambda x: self.share_text(self.input_text.text)
        )
        action_bar_1.add_widget(btn_listen_1)
        action_bar_1.add_widget(btn_copy_1)
        action_bar_1.add_widget(btn_share_1)
        main_layout.add_widget(action_bar_1)

        # --- 5. ზონა 2: ნათარგმნი ტექსტი ---
        main_layout.add_widget(Label(text="თარგმანი (2):", size_hint_y=0.04, font_name=FONT_PATH, halign='left'))
        self.output_text = TextInput(
            hint_text="ნათარგმნი ტექსტი გამოჩნდება აქ...",
            size_hint_y=0.22,
            readonly=True,
            multiline=True,
            font_name=FONT_PATH
        )
        main_layout.add_widget(self.output_text)

        # ზონა 2-ის მოქმედებები
        action_bar_2 = BoxLayout(size_hint_y=0.07, spacing=5)
        btn_listen_2 = Button(
            text="🔊 მოსმენა", 
            font_name=FONT_PATH,
            background_color=(0.2, 0.7, 0.3, 1),
            on_press=lambda x: self.speak_text(self.output_text.text, self.target_lang)
        )
        btn_copy_2 = Button(
            text="📋 დაკოპირება", 
            font_name=FONT_PATH,
            on_press=lambda x: self.copy_to_clipboard(self.output_text.text)
        )
        btn_share_2 = Button(
            text="📲 გაზიარება", 
            font_name=FONT_PATH,
            background_color=(0.8, 0.5, 0.2, 1),
            on_press=lambda x: self.share_text(self.output_text.text)
        )
        action_bar_2.add_widget(btn_listen_2)
        action_bar_2.add_widget(btn_copy_2)
        action_bar_2.add_widget(btn_share_2)
        main_layout.add_widget(action_bar_2)

        # Status Footer
        self.status_label = Label(text="სისტემა მზადაა", size_hint_y=0.04, font_name=FONT_PATH, color=(0.7, 0.7, 0.7, 1))
        main_layout.add_widget(self.status_label)

        return main_layout

    # --- 📲 გაზიარების ფუნქცია ---
    def share_text(self, text):
        if not text.strip():
            self.status_label.text = "⚠️ გასაზიარებელი ტექსტი ცარიელია!"
            return

        if platform == 'android':
            try:
                if share:
                    share.share(text)
                else:
                    from jnius import autoclass
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    Intent = autoclass('android.content.Intent')
                    String = autoclass('java.lang.String')
                    
                    intent = Intent()
                    intent.setAction(Intent.ACTION_SEND)
                    intent.setType("text/plain")
                    intent.putExtra(Intent.EXTRA_TEXT, String(text))
                    
                    chooser = Intent.createChooser(intent, String("გაზიარება:"))
                    PythonActivity.mActivity.startActivity(chooser)
                self.status_label.text = "📲 გაზიარების მენიუ გაიხსნა"
            except Exception as e:
                self.status_label.text = f"გაზიარების შეცდომა: {str(e)}"
        else:
            self.copy_to_clipboard(text)
            self.status_label.text = "📲 ტექსტი დაკოპირდა გაზიარებისთვის!"

    # --- 🔊 გახმოვანება (TTS) ---
    def speak_text(self, text, lang):
        if not text.strip():
            self.status_label.text = "⚠️ ტექსტის ველი ცარიელია!"
            return

        self.status_label.text = f"🔊 მიმდინარეობს გახმოვანება ({lang.upper()})..."

        def run_tts():
            if tts and platform == 'android':
                try:
                    tts.speak(text)
                    return
                except Exception:
                    pass

            try:
                url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={requests.utils.quote(text)}&tl={lang}&client=tw-ob"
                res = requests.get(url, timeout=5)
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

    # --- 📋 დაკოპირება ---
    def copy_to_clipboard(self, text):
        if text.strip():
            if clipboard and platform == 'android':
                clipboard.copy(text)
            else:
                Clipboard.copy(text)
            self.status_label.text = "📋 ტექსტი დაკოპირდა!"
        else:
            self.status_label.text = "⚠️ დასაკოპირებელი ტექსტი არ არის!"

    # --- 📷 კამერის ჩართვა (დატრიალების კორექციით) ---
    def toggle_camera(self, instance):
        if not self.camera_active:
            try:
                self.camera_box.clear_widgets()
                self.camera_obj = Camera(play=True, resolution=(640, 480))
                
                # Android-ზე ტექსტურის 90 გრადუსით გასწორება
                if platform == 'android':
                    Clock.schedule_interval(self._fix_camera_orientation, 1.0 / 30.0)

                self.camera_box.add_widget(self.camera_obj)
                self.camera_active = True
                self.status_label.text = "📷 კამერა ჩართულია"
            except Exception as e:
                self.status_label.text = f"კამერის შეცდომა: {str(e)}"
        else:
            if platform == 'android':
                Clock.unschedule(self._fix_camera_orientation)
            if hasattr(self, 'camera_obj') and self.camera_obj:
                self.camera_obj.play = False
            self.camera_box.clear_widgets()
            self.camera_box.add_widget(self.camera_placeholder)
            self.camera_active = False
            self.status_label.text = "📷 კამერა გათიშულია"

    def _fix_camera_orientation(self, dt):
        if hasattr(self, 'camera_obj') and self.camera_obj.texture:
            # Android-ზე ვერტიკალური ხედვისთვის ტექსტურის კუთხის გასწორება
            self.camera_obj.texture.uvpos = (0, 0)
            self.camera_obj.texture.uvsize = (1, 1)

    # --- მენიუს ფანჯარა (Popup) ---
    def open_menu_popup(self, instance):
        menu_content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # კამერის ზონა
        self.camera_box = BoxLayout(size_hint_y=0.4)
        self.camera_placeholder = Label(text="📷 კამერა გათიშულია.", font_name=FONT_PATH)
        self.camera_box.add_widget(self.camera_placeholder)
        menu_content.add_widget(self.camera_box)

        # ფუნქციების ბადე
        menu_grid = GridLayout(cols=2, spacing=8, size_hint_y=0.5)
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

    # --- 🎙️ ხმოვანი ამოცნობა (STT) ---
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
                elif response.status_code == 401:
                    Clock.schedule_once(lambda dt: self.update_output("API Error 401: განაახლეთ GEMINI_API_KEY!", False))
                else:
                    Clock.schedule_once(lambda dt: self.update_output(f"API Error: {response.status_code}", False))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.update_output(f"ქსელის შეცდომა: {str(e)}", False))

        threading.Thread(target=make_request).start()

    def update_output(self, text, auto_speak):
        self.output_text.text = text
        self.status_label.text = "✅ თარგმანი მზადაა"
        if auto_speak:
            self.speak_text(text, self.target_lang)

    # --- 🔍 Live OCR (ტექსტის ამოცნობა) ---
    def run_ocr(self, instance):
        if self.camera_active and hasattr(self, 'camera_obj') and self.camera_obj:
            try:
                photo_path = os.path.join(self.user_data_dir, "ocr_frame.png") if hasattr(self, 'user_data_dir') else "ocr_frame.png"
                self.camera_obj.export_to_png(photo_path)
                self.status_label.text = "🔍 სურათი გადაღებულია, მიმდინარეობს OCR..."

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

    def show_history(self, instance):
        self.output_text.text = "ისტორია ცარიელია."

if __name__ == "__main__":
    LingoLensApp().run()
