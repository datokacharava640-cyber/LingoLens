from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
import threading
import requests

from config import BACKEND_URL, API_SECRET_KEY, FONT_PATH
from translations import TRANSLATIONS

# კლავიატურის ეკრანზე ამოწევის მართვა
Window.softinput_mode = "below_target"

class LingoLensApp(App):
    def build(self):
        self.current_lang = "ka"  # ნაგულისხმევად ქართული
        self.t = TRANSLATIONS[self.current_lang]

        root = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # სათაური
        self.title_label = Label(
            text=self.t["title"],
            font_size=18,
            font_name=FONT_PATH,
            size_hint=(1, 0.08)
        )
        root.add_widget(self.title_label)
        
        # გამოტანის ველი
        scroll = ScrollView(size_hint=(1, 0.38))
        self.output_label = Label(
            text=self.t["ready"],
            font_size=15,
            font_name=FONT_PATH,
            halign="left",
            valign="top",
            text_size=(350, None)
        )
        self.output_label.bind(
            texture_size=lambda *args: setattr(self.output_label, 'height', self.output_label.texture_size[1])
        )
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)
        
        # შეყვანის ველი და გაგზავნა
        input_layout = BoxLayout(orientation='horizontal', spacing=5, size_hint=(1, 0.12))
        self.text_input = TextInput(
            text=self.t["placeholder"],
            font_name=FONT_PATH,
            multiline=False,
            size_hint=(0.75, 1)
        )
        input_layout.add_widget(self.text_input)
        
        self.send_btn = Button(
            text=self.t["send"],
            font_name=FONT_PATH,
            size_hint=(0.25, 1),
            on_press=self.run_chat_test
        )
        input_layout.add_widget(self.send_btn)
        root.add_widget(input_layout)
        
        # ძირითადი ფუნქციების ღილაკები (სერვერი, OCR, ხმოვანი ჩატი)
        btn_layout = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.12))
        
        self.health_btn = Button(
            text=self.t["server_btn"],
            font_name=FONT_PATH,
            on_press=self.test_server_connection
        )
        btn_layout.add_widget(self.health_btn)
        
        self.ocr_btn = Button(
            text=self.t["ocr_btn"],
            font_name=FONT_PATH,
            on_press=self.run_ocr_test
        )
        btn_layout.add_widget(self.ocr_btn)

        self.voice_btn = Button(
            text="ხმოვანი ჩატი" if self.current_lang == "ka" else "Voice Chat",
            font_name=FONT_PATH,
            on_press=self.run_voice_chat
        )
        btn_layout.add_widget(self.voice_btn)
        
        root.add_widget(btn_layout)

        # ენის გადამრთველი ღილაკი (KA / EN / ES / FR)
        self.lang_toggle_btn = Button(
            text="🌍 Change Language (KA / EN / ES / FR)",
            font_name=FONT_PATH,
            size_hint=(1, 0.10),
            on_press=self.toggle_language
        )
        root.add_widget(self.lang_toggle_btn)

        return root

    def toggle_language(self, instance):
        # ენების ციკლური გადართვა
        langs = list(TRANSLATIONS.keys())
        current_index = langs.index(self.current_lang)
        next_index = (current_index + 1) % len(langs)
        self.current_lang = langs[next_index]

        self.t = TRANSLATIONS[self.current_lang]
        
        # ინტერფეისის დინამიური განახლება
        self.title_label.text = self.t["title"]
        self.output_label.text = self.t["ready"]
        self.send_btn.text = self.t["send"]
        self.health_btn.text = self.t["server_btn"]
        self.ocr_btn.text = self.t["ocr_btn"]
        self.text_input.text = self.t["placeholder"]
        self.voice_btn.text = "ხმოვანი ჩატი" if self.current_lang == "ka" else "Voice Chat"

    def update_output(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', text))

    def test_server_connection(self, instance):
        self.update_output("მიმდინარეობს სერვერთან კავშირის შემოწმება...")
        def task():
            try:
                headers = {"X-API-Key": API_SECRET_KEY}
                response = requests.get(f"{BACKEND_URL}/", headers=headers, timeout=5)
                if response.status_code == 200:
                    self.update_output(f"სერვერი სტაბილურია:\n{response.json()}")
                else:
                    self.update_output(f"სერვერის პასუხი: {response.status_code}")
            except Exception as e:
                self.update_output(f"შეცდომა სერვერთან კავშირისას:\n{str(e)}")
        threading.Thread(target=task).start()

    def run_ocr_test(self, instance):
        self.update_output("მიმდინარეობს თარგმნა...")
        def task():
            try:
                payload = {"text": "გამარჯობა, როგორ ხარ?", "target_lang": self.current_lang}
                response = requests.post(f"{BACKEND_URL}/translate/", json=payload, timeout=5)
                if response.status_code == 200:
                    self.update_output(f"თარგმნის პასუხი:\n{response.json()}")
                else:
                    self.update_output(f"სერვისის პასუხი: {response.status_code}")
            except Exception as e:
                self.update_output(f"შეცდომა სერვისთან კავშირისას:\n{str(e)}")
        threading.Thread(target=task).start()

    def run_chat_test(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        self.update_output(f"იგზავნება AI-თან: {user_text}...")
        
        def task():
            try:
                payload = {"message": user_text}
                response = requests.post(f"{BACKEND_URL}/chat/", json=payload, timeout=8)
                if response.status_code == 200:
                    res_data = response.json()
                    self.update_output(f"AI პასუხი:\n{res_data}")
                else:
                    self.update_output(f"სერვერის შეცდომა: {response.status_code}")
            except Exception as e:
                self.update_output(f"კავშირის შეცდომა:\n{str(e)}")
        threading.Thread(target=task).start()

    def run_voice_chat(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text or user_text == self.t["placeholder"]:
            user_text = "Hello, LingoLens AI is active!"
            
        self.update_output("გენერირდება ხმოვანი პასუხი სერვერზე...")

        def task():
            try:
                payload = {"message": user_text, "lang": self.current_lang}
                response = requests.post(f"{BACKEND_URL}/voice-chat/", json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    reply_text = data.get("reply_text")
                    audio_url = data.get("audio_url")
                    
                    self.update_output(f"ხმოვანი პასუხი:\n{reply_text}\n\nმიმდინარეობს აუდიოს დაკვრა...")
                    
                    # აუდიოს ჩამოტვირთვა და დაკვრა ტელეფონში
                    sound = SoundLoader.load(audio_url)
                    if sound:
                        sound.play()
                    else:
                        self.update_output("ვერ მოხერხდა აუდიო ფაილის ჩატვირთვა.")
                else:
                    self.update_output(f"სერვერის შეცდომა: {response.status_code}")
            except Exception as e:
                self.update_output(f"ხმოვანი ჩატის შეცდომა:\n{str(e)}")

        threading.Thread(target=task).start()

if __name__ == '__main__':
    LingoLensApp().run()
