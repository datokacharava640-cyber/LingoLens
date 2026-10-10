from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
import threading
import requests
import os

# 1. უსაფრთხო იმპორტი config-დან
try:
    from config import BACKEND_URL, API_SECRET_KEY, FONT_PATH
except Exception:
    BACKEND_URL = "http://37.27.255.1:8000"
    API_SECRET_KEY = ""
    FONT_PATH = None

# 2. უსაფრთხო იმპორტი translations-დან
try:
    from translations import TRANSLATIONS
except Exception:
    TRANSLATIONS = {
        "ka": {
            "title": "LingoLens AI",
            "ready": "სისტემა მზადაა...",
            "send": "გაგზავნა",
            "server_btn": "სერვერი",
            "ocr_btn": "თარგმანი",
            "placeholder": "ჩაწერეთ ტექსტი..."
        }
    }

# 3. უსაფრთხო აუდიო იმპორტი
try:
    from kivy.core.audio import SoundLoader
except Exception:
    SoundLoader = None

Window.softinput_mode = "below_target"

class LingoLensApp(App):
    def build(self):
        self.current_lang = "ka"
        self.t = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["ka"])

        # ფონტის უსაფრთხო შემოწმება
        self.font_to_use = None
        if FONT_PATH and os.path.exists(FONT_PATH):
            self.font_to_use = FONT_PATH

        root = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # სათაური
        self.title_label = Label(
            text=str(self.t.get("title", "LingoLens AI")),
            font_size=18,
            font_name=self.font_to_use,
            size_hint=(1, 0.08)
        )
        root.add_widget(self.title_label)
        
        # გამოტანის ველი
        scroll = ScrollView(size_hint=(1, 0.38))
        self.output_label = Label(
            text=str(self.t.get("ready", "მზადაა...")),
            font_size=15,
            font_name=self.font_to_use,
            halign="left",
            valign="top",
            text_size=(350, None)
        )
        self.output_label.bind(
            texture_size=lambda *args: setattr(self.output_label, 'height', self.output_label.texture_size[1])
        )
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)
        
        # შეყვანის ველი
        input_layout = BoxLayout(orientation='horizontal', spacing=5, size_hint=(1, 0.12))
        self.text_input = TextInput(
            text=str(self.t.get("placeholder", "")),
            font_name=self.font_to_use,
            multiline=False,
            size_hint=(0.75, 1)
        )
        input_layout.add_widget(self.text_input)
        
        self.send_btn = Button(
            text=str(self.t.get("send", "გაგზავნა")),
            font_name=self.font_to_use,
            size_hint=(0.25, 1),
            on_press=self.run_chat_test
        )
        input_layout.add_widget(self.send_btn)
        root.add_widget(input_layout)
        
        # ღილაკების განლაგება
        btn_layout = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.12))
        
        self.health_btn = Button(
            text=str(self.t.get("server_btn", "სერვერი")),
            font_name=self.font_to_use,
            on_press=self.test_server_connection
        )
        btn_layout.add_widget(self.health_btn)
        
        self.ocr_btn = Button(
            text=str(self.t.get("ocr_btn", "თარგმანი")),
            font_name=self.font_to_use,
            on_press=self.run_ocr_test
        )
        btn_layout.add_widget(self.ocr_btn)

        self.voice_btn = Button(
            text="ხმოვანი ჩატი" if self.current_lang == "ka" else "Voice Chat",
            font_name=self.font_to_use,
            on_press=self.run_voice_chat
        )
        btn_layout.add_widget(self.voice_btn)
        
        root.add_widget(btn_layout)

        # ენის გადამრთველი ღილაკი
        self.lang_toggle_btn = Button(
            text="🌍 Change Language (KA / EN / ES / FR)",
            font_name=self.font_to_use,
            size_hint=(1, 0.10),
            on_press=self.toggle_language
        )
        root.add_widget(self.lang_toggle_btn)

        return root

    def toggle_language(self, instance):
        langs = list(TRANSLATIONS.keys())
        if self.current_lang in langs:
            idx = (langs.index(self.current_lang) + 1) % len(langs)
            self.current_lang = langs[idx]
        else:
            self.current_lang = "ka"

        self.t = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["ka"])
        
        self.title_label.text = str(self.t.get("title", "LingoLens AI"))
        self.output_label.text = str(self.t.get("ready", "მზადაა..."))
        self.send_btn.text = str(self.t.get("send", "გაგზავნა"))
        self.health_btn.text = str(self.t.get("server_btn", "სერვერი"))
        self.ocr_btn.text = str(self.t.get("ocr_btn", "თარგმანი"))
        self.text_input.text = str(self.t.get("placeholder", ""))
        self.voice_btn.text = "ხმოვანი ჩატი" if self.current_lang == "ka" else "Voice Chat"

    def update_output(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def test_server_connection(self, instance):
        self.update_output("მიმდინარეობს კავშირის შემოწმება...")
        def task():
            try:
                headers = {"X-API-Key": API_SECRET_KEY}
                response = requests.get(f"{BACKEND_URL}/", headers=headers, timeout=5)
                if response.status_code == 200:
                    self.update_output(f"სერვერი ჩართულია:\n{response.json()}")
                else:
                    self.update_output(f"სერვერის სტატუსი: {response.status_code}")
            except Exception as e:
                self.update_output(f"კავშირის შეცდომა:\n{str(e)}")
        threading.Thread(target=task).start()

    def run_ocr_test(self, instance):
        self.update_output("მიმდინარეობს თარგმნა...")
        def task():
            try:
                payload = {"text": "გამარჯობა", "target_lang": self.current_lang}
                response = requests.post(f"{BACKEND_URL}/translate/", json=payload, timeout=5)
                if response.status_code == 200:
                    self.update_output(f"პასუხი:\n{response.json()}")
                else:
                    self.update_output(f"შეცდომა: {response.status_code}")
            except Exception as e:
                self.update_output(f"შეცდომა:\n{str(e)}")
        threading.Thread(target=task).start()

    def run_chat_test(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        self.update_output(f"იგზავნება: {user_text}...")
        
        def task():
            try:
                payload = {"message": user_text}
                response = requests.post(f"{BACKEND_URL}/chat/", json=payload, timeout=8)
                if response.status_code == 200:
                    self.update_output(f"AI:\n{response.json()}")
                else:
                    self.update_output(f"შეცდომა: {response.status_code}")
            except Exception as e:
                self.update_output(f"შეცდომა:\n{str(e)}")
        threading.Thread(target=task).start()

    def run_voice_chat(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            user_text = "Hello"
            
        self.update_output("მუშავდება ხმოვანი პასუხი...")

        def task():
            try:
                payload = {"message": user_text, "lang": self.current_lang}
                response = requests.post(f"{BACKEND_URL}/voice-chat/", json=payload, timeout=12)
                if response.status_code == 200:
                    data = response.json()
                    reply_text = data.get("reply_text", "")
                    audio_url = data.get("audio_url", "")
                    
                    self.update_output(f"პასუხი:\n{reply_text}\n\nაუდიო იტვირთება...")
                    
                    if audio_url and SoundLoader:
                        audio_res = requests.get(audio_url, timeout=10)
                        if audio_res.status_code == 200:
                            local_filename = os.path.join(self.user_data_dir, "temp_voice.mp3")
                            with open(local_filename, "wb") as f:
                                f.write(audio_res.content)
                            
                            def play_sound(dt):
                                try:
                                    sound = SoundLoader.load(local_filename)
                                    if sound:
                                        sound.play()
                                except Exception as err:
                                    print(f"Audio Play error: {err}")
                            Clock.schedule_once(play_sound, 0.1)
                else:
                    self.update_output(f"სერვერის შეცდომა: {response.status_code}")
            except Exception as e:
                self.update_output(f"ხმის შეცდომა:\n{str(e)}")

        threading.Thread(target=task).start()

if __name__ == '__main__':
    LingoLensApp().run()
