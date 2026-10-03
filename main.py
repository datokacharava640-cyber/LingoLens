from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
import requests

try:
    from android.permissions import request_permissions, Permission
except ImportError:
    pass

# შენი Hetzner სერვერის ზუსტი მისამართი (მიუთითე პორტი, მაგალითად 8000)
BACKEND_URL = "http://37.27.255.1:8000"

class LingoLensApp(App):
    def build(self):
        self.request_android_permissions()

        root_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        font_path = "font.ttf"  # ქართული ფონტი

        # სათაური
        self.title_label = Label(
            text="LingoLens AI - უშეცდომო თარგმანი & დიალოგი", 
            font_name=font_path, 
            font_size=18,
            size_hint_y=None, 
            height=40
        )
        root_layout.add_widget(self.title_label)

        # შედეგის გამოსატენი ველი (სქროლვადი)
        scroll = ScrollView(size_hint=(1, 0.35))
        self.result_label = Label(
            text="აირჩიეთ ფუნქცია და ჩაწერეთ ტექსტი...", 
            font_name=font_path, 
            font_size=15,
            halign='center',
            valign='middle'
        )
        self.result_label.bind(texture_size=self.result_label.setter('texture_size'))
        scroll.add_widget(self.result_label)
        root_layout.add_widget(scroll)

        # ტექსტის შეყვანის ველი
        self.input_field = TextInput(
            hint_text="ჩაწერეთ ტექსტი თარგმნისთვის ან დიალოგისთვის...", 
            font_name=font_path,
            size_hint_y=None, 
            height=50
        )
        root_layout.add_widget(self.input_field)

        # 1. სრული გრამატიკული თარგმანის ღილაკი
        btn_translate = Button(text="სრული გრამატიკული თარგმანი (ყველა ენა)", font_name=font_path, size_hint_y=None, height=45)
        btn_translate.bind(on_press=self.strict_grammar_translate)
        root_layout.add_widget(btn_translate)

        # 2. ორმხრივი დიალოგი (ჩატი)
        btn_chat = Button(text="AI ორმხრივი დიალოგი", font_name=font_path, size_hint_y=None, height=45)
        btn_chat.bind(on_press=self.send_chat_message)
        root_layout.add_widget(btn_chat)

        # 3. კამერისა და ფოტოს თარგმნა
        btn_ocr = Button(text="ფოტოს / კამერის თარგმნა", font_name=font_path, size_hint_y=None, height=45)
        btn_ocr.bind(on_press=self.translate_camera_photo)
        root_layout.add_widget(btn_ocr)

        # 4. მხარდაჭერილი ენები
        btn_langs = Button(text="მხარდაჭერილი ენები", font_name=font_path, size_hint_y=None, height=45)
        btn_langs.bind(on_press=self.fetch_languages)
        root_layout.add_widget(btn_langs)

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
            # სერვერზე ვგზავნით ტექსტს უშეცდომო გრამატიკული თარგმანისთვის
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
        self.result_label.text = "კამერის რეჟიმი მუშაობს..."
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

if __name__ == '__main__':
    LingoLensApp().run()
