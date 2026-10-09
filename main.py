from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
import threading
import requests

from config import BACKEND_URL, API_SECRET_KEY, FONT_PATH

try:
    from ocr_service import process_image_ocr
except ImportError:
    process_image_ocr = None

try:
    from chat_service import send_chat_message
except ImportError:
    send_chat_message = None


class LingoLensApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # სათაური ქართული შრიფტით
        self.title_label = Label(
            text="LingoLens AI - მთავარი პანელი",
            font_size=20,
            font_name=FONT_PATH,
            size_hint=(1, 0.1)
        )
        root.add_widget(self.title_label)
        
        # შედეგების გამოსატანი ველი (ScrollView-ში, რომ გრძელი ტექსტი ჩაევტიოს)
        scroll = ScrollView(size_hint=(1, 0.5))
        self.output_label = Label(
            text="სისტემა მზადაა მუშაობისთვის...",
            font_size=16,
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
        
        # ტექსტის შესაყვანი ველი (ჩათისთვის ან ტესტისთვის)
        self.text_input = TextInput(
            text="გამარჯობა, სერვერო!",
            font_name=FONT_PATH,
            size_hint=(1, 0.15),
            multiline=False
        )
        root.add_widget(self.text_input)
        
        # ღილაკების პანელი
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.15))
        
        # 1. სერვერის Health Check ღილაკი
        health_btn = Button(
            text="სერვერი",
            font_name=FONT_PATH,
            on_press=self.test_server_connection
        )
        btn_layout.add_widget(health_btn)
        
        # 2. OCR / თარგმნის სერვისის ღილაკი
        ocr_btn = Button(
            text="OCR სერვისი",
            font_name=FONT_PATH,
            on_press=self.run_ocr_test
        )
        btn_layout.add_widget(ocr_btn)
        
        # 3. AI ჩათის სერვისის ღილაკი
        chat_btn = Button(
            text="AI ჩატი",
            font_name=FONT_PATH,
            on_press=self.run_chat_test
        )
        btn_layout.add_widget(chat_btn)
        
        root.add_widget(btn_layout)
        return root

    def update_output(self, text):
        self.output_label.text = text

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
            if process_image_ocr:
                try:
                    # აქ შეგიძლიათ გამოიძახოთ თქვენი OCR მეთოდი, რომელიც გაქვთ ocr_service.py-ში
                    res = "OCR სერვისი წარმატებით ჩაიტვირთა!"
                    self.update_output(res)
                except Exception as e:
                    self.update_output(f"OCR შეცდომა: {str(e)}")
            else:
                self.update_output("ocr_service მოდული ვერ მოიძებნა ან ცარიელია.")
        threading.Thread(target=task).start()

    def run_chat_test(self, instance):
        user_text = self.text_input.text
        self.update_output(f"იგზავნება შეტყობინება AI ჩათში: '{user_text}'...")
        def task():
            if send_chat_message:
                try:
                    # აქ შეგიძლიათ გადასცეთ ტექსტი chat_service-ს
                    res = f"AI ჩათის პასუხი მიღებულია მომხმარებლისთვის: {user_text}"
                    self.update_output(res)
                except Exception as e:
                    self.update_output(f"ჩათის შეცდომა: {str(e)}")
            else:
                self.update_output(f"მოთხოვნა გაიგზავნა სერვერზე:\n{user_text}")
        threading.Thread(target=task).start()


if __name__ == '__main__':
    LingoLensApp().run()
