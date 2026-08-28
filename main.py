import os
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

class LingoLensApp(App):
    def build(self):
        self.server_url = "https://lingo-lens-eight.vercel.app"
        
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # სათაური
        title_label = Label(
            text="LingoLens Ultra Pro",
            font_size='22sp',
            bold=True,
            size_hint=(1, 0.1)
        )
        layout.add_widget(title_label)

        # ტექსტის შესაყვანი ველები
        self.input_text = TextInput(
            hint_text="შეიყვანეთ ტექსტი სათარგმნად...",
            multiline=True,
            size_hint=(1, 0.4)
        )
        layout.add_widget(self.input_text)

        # თარგმნის ღილაკი
        btn_translate = Button(
            text="თარგმნა (Vercel API)",
            size_hint=(1, 0.12),
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_translate.bind(on_press=self.translate_text)
        layout.add_widget(btn_translate)

        # შედეგის გამოსატანი ველი
        self.result_label = Label(
            text="შედეგი გამოჩნდება აქ",
            halign="center",
            valign="middle",
            size_hint=(1, 0.38)
        )
        self.result_label.bind(size=self.result_label.setter('text_size'))
        layout.add_widget(self.result_label)

        return layout

    def translate_text(self, instance):
        text_to_translate = self.input_text.text.strip()
        if not text_to_translate:
            self.result_label.text = "გთხოვთ, შეიყვანოთ ტექსტი!"
            return

        self.result_label.text = "მიმდინარეობს თარგმნა..."
        
        # API მოთხოვნა Vercel სერვერზე
        try:
            response = requests.post(
                f"{self.server_url}/api/index",
                json={"text": text_to_translate},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.result_label.text = data.get("translated_text", "თარგმნა ვერ მოხერხდა")
            else:
                self.result_label.text = f"სერვერის შეცდომა: {response.status_code}"
        except Exception as e:
            self.result_label.text = f"კავშირის შეცდომა: {str(e)}"

if __name__ == "__main__":
    LingoLensApp().run()
