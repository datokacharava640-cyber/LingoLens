from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import requests

try:
    from android.permissions import request_permissions, Permission
except ImportError:
    pass

# აქ ჩაწერე შენი აწყობილი სერვერის ლინკი (მაგ: Vercel-ის მისამართი)
BACKEND_URL = "https://your-backend-url.vercel.app"

class LingoLensApp(App):
    def build(self):
        # ანდროიდის ნებართვების მოთხოვნა გაშვებისას
        self.request_android_permissions()

        layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        # ფონტის ფაილი, რომელიც პროექტში უნდა იდოს
        font_path = "DejaVuSans.ttf"
        
        self.label = Label(
            text="მოგესალმებით LingoLens AI-ში!", 
            font_name=font_path, 
            font_size=18
        )
        layout.add_widget(self.label)
        
        self.input_field = TextInput(
            hint_text="ჩაწერეთ შეტყობინება...", 
            font_name=font_path,
            size_hint_y=None, 
            height=50
        )
        layout.add_widget(self.input_field)
        
        btn_chat = Button(
            text="შეტყობინების გაგზავნა", 
            font_name=font_path,
            size_hint_y=None, 
            height=50
        )
        btn_chat.bind(on_press=self.send_chat)
        layout.add_widget(btn_chat)
        
        btn_status = Button(
            text="სერვერის სტატუსი", 
            font_name=font_path,
            size_hint_y=None, 
            height=50
        )
        btn_status.bind(on_press=self.check_status)
        layout.add_widget(btn_status)
        
        return layout

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

    def send_chat(self, instance):
        message = self.input_field.text
        if not message:
            self.label.text = "გთხოვთ შეიყვანოთ ტექსტი!"
            return
        try:
            response = requests.post(f"{BACKEND_URL}/chat/", json={"message": message})
            if response.status_code == 200:
                self.label.text = f"პასუხი: {response.json()}"
            else:
                self.label.text = "შეცდომა სერვერის პასუხში."
        except Exception as e:
            self.label.text = f"ვერ უკავშირდება სერვერს: {e}"

    def check_status(self, instance):
        try:
            response = requests.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                self.label.text = f"სტატუსი: {response.json()}"
            else:
                self.label.text = "სერვერი მიუწვდომელია."
        except Exception as e:
            self.label.text = f"შეცდომა: {e}"

if __name__ == '__main__':
    LingoLensApp().run()
