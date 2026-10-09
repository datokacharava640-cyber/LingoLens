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

from config import BACKEND_URL, API_SECRET_KEY, FONT_PATH

# კლავიატურის ეკრანზე ამოწევის მართვა
Window.softinput_mode = "below_target"

try:
    from languages import LANGUAGES_LIST
except ImportError:
    LANGUAGES_LIST = ["ქართული", "English", "Español"]


class LingoLensApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        self.title_label = Label(
            text="LingoLens AI - მთავარი პანელი",
            font_size=18,
            font_name=FONT_PATH,
            size_hint=(1, 0.08)
        )
        root.add_widget(self.title_label)
        
        scroll = ScrollView(size_hint=(1, 0.45))
        self.output_label = Label(
            text="სისტემა მზადაა მუშაობისთვის...",
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
        
        langs_text = " ხელმისაწვდომი ენები: " + ", ".join(LANGUAGES_LIST[:5])
        self.lang_label = Label(
            text=langs_text,
            font_size=13,
            font_name=FONT_PATH,
            size_hint=(1, 0.06)
        )
        root.add_widget(self.lang_label)
        
        input_layout = BoxLayout(orientation='horizontal', spacing=5, size_hint=(1, 0.12))
        
        self.text_input = TextInput(
            text="გამარჯობა, სერვერო!",
            font_name=FONT_PATH,
            multiline=False,
            size_hint=(0.75, 1)
        )
        input_layout.add_widget(self.text_input)
        
        send_btn = Button(
            text="გაგზავნა",
            font_name=FONT_PATH,
            size_hint=(0.25, 1),
            on_press=self.run_chat_test
        )
        input_layout.add_widget(send_btn)
        root.add_widget(input_layout)
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.12))
        
        health_btn = Button(
            text="სერვერი",
            font_name=FONT_PATH,
            on_press=self.test_server_connection
        )
        btn_layout.add_widget(health_btn)
        
        ocr_btn = Button(
            text="OCR სერვისი",
            font_name=FONT_PATH,
            on_press=self.run_ocr_test
        )
        btn_layout.add_widget(ocr_btn)
        
        root.add_widget(btn_layout)
        return root

    def update_output(self, text):
        # Clock-ის გამოყენება უზრუნველყოფს ინტერფეისის უსაფრთხო განახლებას ფონური ნაკადიდან
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
        self.update_output("მიმდინარეობს OCR სერვისის ტესტირება...")
        def task():
            try:
                payload = {"text": "ტესტი", "target_lang": "en"}
                response = requests.post(f"{BACKEND_URL}/translate/", json=payload, timeout=5)
                if response.status_code == 200:
                    self.update_output(f"OCR/თარგმნის პასუხი:\n{response.json()}")
                else:
                    self.update_output(f"სერვისის პასუხი: {response.status_code}")
            except Exception as e:
                self.update_output(f"შეცდომა სერვისთან კავშირისას:\n{str(e)}")
        threading.Thread(target=task).start()

    def run_chat_test(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        self.update_output(f"იგზავნება სერვერზე: {user_text}...")
        
        def task():
            try:
                payload = {"message": user_text}
                response = requests.post(f"{BACKEND_URL}/chat/", json=payload, timeout=8)
                if response.status_code == 200:
                    res_data = response.json()
                    self.update_output(f"სერვერის პასუხი:\n{res_data}")
                else:
                    self.update_output(f"სერვერის შეცდომა: {response.status_code}")
            except Exception as e:
                self.update_output(f"კავშირის შეცდომა:\n{str(e)}")
                
        threading.Thread(target=task).start()


if __name__ == '__main__':
    LingoLensApp().run()
