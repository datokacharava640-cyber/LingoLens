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
import traceback

# 1. Adiresy sy fanamarinana ny server sy font
BACKEND_URL = "http://37.27.255.1:8000"

try:
    from config import API_SECRET_KEY, FONT_PATH
except Exception:
    API_SECRET_KEY = ""
    FONT_PATH = "font.ttf"

if not FONT_PATH or not os.path.exists(FONT_PATH):
    if os.path.exists("font.ttf"):
        FONT_PATH = "font.ttf"
    else:
        FONT_PATH = None

# 2. Dikanteny azo antoka
try:
    from translations import TRANSLATIONS
except Exception:
    TRANSLATIONS = {
        "ka": {
            "title": "LingoLens AI - Hetzner",
            "ready": "სისტემა მზადაა...",
            "send": "გაგზავნა",
            "server_btn": "სერვერი",
            "translate_btn": "თარგმანი",
            "placeholder": "ჩაწერეთ ტექსტი..."
        }
    }

# 3. SoundLoader
try:
    from kivy.core.audio import SoundLoader
except Exception:
    SoundLoader = None

Window.softinput_mode = "below_target"

class LingoLensApp(App):
    def build(self):
        try:
            self.current_lang = "ka"
            self.t = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["ka"])

            self.font_to_use = FONT_PATH if (FONT_PATH and os.path.exists(FONT_PATH)) else None
            font_kwargs = {'font_name': self.font_to_use} if self.font_to_use else {}

            root = BoxLayout(orientation='vertical', padding=15, spacing=10)
            
            # Lohateny
            self.title_label = Label(
                text=str(self.t.get("title", "LingoLens AI")),
                font_size=18,
                size_hint=(1, 0.08),
                **font_kwargs
            )
            root.add_widget(self.title_label)
            
            # Vata famoahana vokatra
            scroll = ScrollView(size_hint=(1, 0.38))
            self.output_label = Label(
                text=str(self.t.get("ready", "მზადაა...")),
                font_size=15,
                halign="left",
                valign="top",
                text_size=(350, None),
                **font_kwargs
            )
            self.output_label.bind(
                texture_size=lambda *args: setattr(self.output_label, 'height', self.output_label.texture_size[1])
            )
            scroll.add_widget(self.output_label)
            root.add_widget(scroll)
            
            # Vata fampidirana soratra
            input_layout = BoxLayout(orientation='horizontal', spacing=5, size_hint=(1, 0.12))
            self.text_input = TextInput(
                text=str(self.t.get("placeholder", "")),
                multiline=False,
                size_hint=(0.75, 1),
                **font_kwargs
            )
            input_layout.add_widget(self.text_input)
            
            self.send_btn = Button(
                text=str(self.t.get("send", "გაგზავნა")),
                size_hint=(0.25, 1),
                on_press=self.send_chat,
                **font_kwargs
            )
            input_layout.add_widget(self.send_btn)
            root.add_widget(input_layout)
            
            # Bokotra fiasana
            btn_layout = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.12))
            
            self.health_btn = Button(
                text=str(self.t.get("server_btn", "სერვერი")),
                on_press=self.check_server,
                **font_kwargs
            )
            btn_layout.add_widget(self.health_btn)
            
            self.translate_btn = Button(
                text=str(self.t.get("translate_btn", "თარგმანი")),
                on_press=self.send_translate,
                **font_kwargs
            )
            btn_layout.add_widget(self.translate_btn)

            self.voice_btn = Button(
                text="ხმოვანი ჩატი" if self.current_lang == "ka" else "Voice Chat",
                on_press=self.run_voice_chat,
                **font_kwargs
            )
            btn_layout.add_widget(self.voice_btn)
            
            root.add_widget(btn_layout)

            # Bokotra fanovana fiteny
            self.lang_toggle_btn = Button(
                text="🌍 Change Language (KA / EN / ES / FR)",
                size_hint=(1, 0.10),
                on_press=self.toggle_language,
                **font_kwargs
            )
            root.add_widget(self.lang_toggle_btn)

            return root

        except Exception as e:
            err_msg = traceback.format_exc()
            error_root = BoxLayout(orientation='vertical', padding=20)
            error_label = Label(text=f"CRASH:\n{err_msg}", font_size=12, halign="left", valign="top")
            error_label.bind(texture_size=lambda *args: setattr(error_label, 'text_size', error_label.size))
            error_root.add_widget(error_label)
            return error_root

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
        self.translate_btn.text = str(self.t.get("translate_btn", "თარგმანი"))
        self.text_input.text = str(self.t.get("placeholder", ""))
        self.voice_btn.text = "ხმოვანი ჩატი" if self.current_lang == "ka" else "Voice Chat"

    def update_output(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def check_server(self, instance):
        self.update_output("მიმდინარეობს სერვერის სტატუსის შემოწმება...")
        def task():
            try:
                res = requests.get(f"{BACKEND_URL}/", timeout=5)
                if res.status_code == 200:
                    self.update_output(f"სერვერი აქტიურია:\n{res.json()}")
                else:
                    self.update_output(f"სერვერის სტატუსი: {res.status_code}")
            except Exception as e:
                self.update_output(f"კავშირის შეცდომა:\n{str(e)}")
        threading.Thread(target=task).start()

    def send_chat(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        self.update_output(f"იგზავნება სერვერზე: {user_text}...")
        
        def task():
            try:
                payload = {"message": user_text}
                res = requests.post(f"{BACKEND_URL}/chat/", json=payload, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    reply = data.get("reply", data.get("reply_text", str(data)))
                    self.update_output(f"AI პასუხი:\n{reply}")
                else:
                    self.update_output(f"შეცდომა {res.status_code}:\n{res.text}")
            except Exception as e:
                self.update_output(f"კავშირის შეცდომა:\n{str(e)}")
        threading.Thread(target=task).start()

    def send_translate(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            user_text = "გამარჯობა"
        self.update_output(f"მიმდინარეობს თარგმნა...")
        
        def task():
            try:
                payload = {"text": user_text, "target_lang": "en"}
                res = requests.post(f"{BACKEND_URL}/translate/", json=payload, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    translation = data.get("translation", "")
                    self.update_output(f"ნათარგმნი (EN):\n{translation}")
                else:
                    self.update_output(f"შეცდომა {res.status_code}:\n{res.text}")
            except Exception as e:
                self.update_output(f"კავშირის შეცდომა:\n{str(e)}")
        threading.Thread(target=task).start()

    def run_voice_chat(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            user_text = "Hello"
            
        self.update_output("მუშავდება ხმოვანი პასუხი...")

        def task():
            try:
                payload = {"message": user_text, "lang": self.current_lang}
                res = requests.post(f"{BACKEND_URL}/voice-chat/", json=payload, timeout=12)
                if res.status_code == 200:
                    data = res.json()
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
                    self.update_output(f"სერვერის შეცდომა: {res.status_code}")
            except Exception as e:
                self.update_output(f"ხმის შეცდომა:\n{str(e)}")

        threading.Thread(target=task).start()

if __name__ == '__main__':
    LingoLensApp().run()
