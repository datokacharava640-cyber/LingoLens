from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
import requests
from config import BACKEND_URL, API_SECRET_KEY

class LingoLensApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        self.label = Label(
            text="LingoLens მზადაა სერვერთან დასაკავშირებლად!", 
            font_size=18,
            font_name="font.ttf",
            halign="center"
        )
        self.layout.add_widget(self.label)
        
        btn = Button(
            text="სერვერის შემოწმება (Health Check)", 
            font_name="font.ttf",
            size_hint=(1, 0.3)
        )
        btn.bind(on_press=self.check_server)
        self.layout.add_widget(btn)
        
        return self.layout

    def check_server(self, instance):
        self.label.text = "მიმდინარეობს სერვერთან დაკავშირება..."
        try:
            headers = {"X-API-Key": API_SECRET_KEY}
            response = requests.get(f"{BACKEND_URL}/", headers=headers, timeout=5)
            if response.status_code == 200:
                self.label.text = f"წარმატება! სერვერი პასუხობს:\n{response.json()}"
            else:
                self.label.text = f"სერვერის შეცდომა: კოდი {response.status_code}"
        except Exception as e:
            self.label.text = f"კავშირი ვერ დამყარდა:\n{str(e)}"

if __name__ == '__main__':
    LingoLensApp().run()
