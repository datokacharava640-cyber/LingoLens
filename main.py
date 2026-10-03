from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
import requests

try:
    from android.permissions import request_permissions, Permission
except ImportError:
    pass

BACKEND_URL = "http://37.27.255.1:8000"

class LingoLensApp(App):
    def build(self):
        self.request_android_permissions()

        root_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        font_path = "font.ttf"

        self.title_label = Label(
            text="LingoLens AI - სრული მართვის პანელი", 
            font_name=font_path, 
            font_size=16,
            size_hint_y=None, 
            height=35
        )
        root_layout.add_widget(self.title_label)

        scroll = ScrollView(size_hint=(1, 0.25))
        self.result_label = Label(
            text="სისტემა მზადაა. აირჩიეთ ფუნქცია...", 
            font_name=font_path, 
            font_size=14,
            halign='center',
            valign='middle'
        )
        self.result_label.bind(texture_size=self.result_label.setter('texture_size'))
        scroll.add_widget(self.result_label)
        root_layout.add_widget(scroll)

        self.input_field = TextInput(
            hint_text="ჩაწერეთ ტექსტი, ნომერი ან შეტყობინება...", 
            font_name=font_path,
            size_hint_y=None, 
            height=45
        )
        root_layout.add_widget(self.input_field)

        # 2x3 ბადის განლაგება (Grid Layout) 6 ძირითადი მოდულისთვის
        grid_menu = GridLayout(cols=2, spacing=8, size_hint_y=None, height=250)

        btn_translator = Button(text="მთარგმნელი", font_name=font_path)
        btn_translator.bind(on_press=self.strict_grammar_translate)
        grid_menu.add_widget(btn_translator)

        btn_dialogue = Button(text="დიალოგი", font_name=font_path)
        btn_dialogue.bind(on_press=self.send_chat_message)
        grid_menu.add_widget(btn_dialogue)

        btn_grammar = Button(text="გრამატიკა", font_name=font_path)
        btn_grammar.bind(on_press=self.strict_grammar_translate)
        grid_menu.add_widget(btn_grammar)

        btn_ocr = Button(text="ლაივ კამერა / OCR", font_name=font_path)
        btn_ocr.bind(on_press=self.translate_camera_photo)
        grid_menu.add_widget(btn_ocr)

        btn_history = Button(text="ისტორია", font_name=font_path)
        btn_history.bind(on_press=self.fetch_languages)
        grid_menu.add_widget(btn_history)

        btn_settings = Button(text="პარამეტრები", font_name=font_path)
        btn_settings.bind(on_press=self.check_for_updates)
        grid_menu.add_widget(btn_settings)

        root_layout.add_widget(grid_menu)

        return root_layout

    def request_android_permissions(self):
        try:
            request_permissions([
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.SEND_SMS,
                Permission.READ_SMS,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
        except Exception:
            pass

    def strict_grammar_translate(self, instance):
        text = self.input_field.text.strip()
        if not text:
            self.result_label.text = "გთხოვთ შეიყვანოთ ტექსტი თარგმნისთვის!"
            return
        try:
            res = requests.post(f"{BACKEND_URL}/translate/", json={"text": text, "target_lang": "en"})
            if res.status_code == 200:
                data = res.json()
                self.result_label.text = f"უშეცდომო თარგმანი:\n{data.get('translation', data)}"
            else:
                self.result_label.text = f"სერვერის შეცდომა: {res.status_code}"
        except Exception as e:
            self.result_label.text = f"ვერ დაკავშირდა სერვერთან: {e}"

    def send_chat_message(self, instance):
        msg = self.input_field.text.strip()
        if not msg:
            self.result_label.text = "შეიყვანეთ შეტყობინება დიალოგისთვის!"
            return
        try:
            res = requests.post(f"{BACKEND_URL}/chat/", json={"message": msg})
            if res.status_code == 200:
                self.result_label.text = f"AI პასუხი:\n{res.json().get('response', res.json())}"
            else:
                self.result_label.text = "შეცდომა დიალოგისას."
        except Exception as e:
            self.result_label.text = f"კავშირის შეცდომა: {e}"

    def translate_camera_photo(self, instance):
        self.result_label.text = "კამერისა და ფოტოს თარგმნის რეჟიმი აქტიურია..."
        try:
            res = requests.get(f"{BACKEND_URL}/offline-status/")
            self.result_label.text = f"სტატუსი: {res.json()}"
        except Exception as e:
            self.result_label.text = f"შეცდომა: {e}"

    def fetch_languages(self, instance):
        try:
            res = requests.get(f"{BACKEND_URL}/languages/")
            self.result_label.text = f"მხარდაჭერილი ენები:\n{res.json()}"
        except Exception as e:
            self.result_label.text = f"შეცდომა: {e}"

    def check_for_updates(self, instance):
        try:
            res = requests.get(f"{BACKEND_URL}/check-update/")
            if res.status_code == 200:
                data = res.json()
                server_version = data.get("latest_version")
                apk_url = data.get("apk_url")
                notes = data.get("release_notes")
                
                current_version = "1.0"
                if server_version != current_version:
                    self.result_label.text = f"ახალი ვერსია ხელმისაწვდომია: {server_version}\n{notes}\nბმული: {apk_url}"
                else:
                    self.result_label.text = "აპლიკაცია არის უახლესი ვერსია!"
            else:
                self.result_label.text = "ვერ მოხერხდა განახლების შემოწმება."
        except Exception as e:
            self.result_label.text = f"შეცდომა: {e}"

if __name__ == '__main__':
    LingoLensApp().run()
