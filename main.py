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

# ზუსტი და სტაბილური Google Gemini API მისამართი და გასაღები
GEMINI_API_KEY = "AQ.Ab8RN6JJSsFMn2prUcWLyEJ2rPUACvXTKdaP0A6bFJwhlaqXrw"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# ქართული ფონტის შემოწმება
FONT_PATH = "font.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = None

# ტექსტები და თარგმანები
TRANSLATIONS = {
    "ka": {
        "title": "LingoLens AI - მთავარი პანელი",
        "ready": "სისტემა მზადაა...",
        "send": "გაგზავნა",
        "status_btn": "სტატუსი",
        "translate_btn": "თარგმანი",
        "placeholder": "ჩაწერეთ ტექსტი..."
    }
}

Window.softinput_mode = "below_target"

class LingoLensApp(App):
    def build(self):
        try:
            self.current_lang = "ka"
            self.t = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["ka"])

            self.font_to_use = FONT_PATH if (FONT_PATH and os.path.exists(FONT_PATH)) else None
            font_kwargs = {'font_name': self.font_to_use} if self.font_to_use else {}

            root = BoxLayout(orientation='vertical', padding=15, spacing=10)
            
            # სათაური
            self.title_label = Label(
                text=str(self.t.get("title", "LingoLens AI")),
                font_size=18,
                size_hint=(1, 0.08),
                **font_kwargs
            )
            root.add_widget(self.title_label)
            
            # პასუხის გამოსატანი ველი
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
            
            # ტექსტის შესაყვანი ველი
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
                on_press=self.run_gemini_chat,
                **font_kwargs
            )
            input_layout.add_widget(self.send_btn)
            root.add_widget(input_layout)
            
            # ღილაკები
            btn_layout = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.12))
            
            self.health_btn = Button(
                text=str(self.t.get("status_btn", "სტატუსი")),
                on_press=self.test_gemini_status,
                **font_kwargs
            )
            btn_layout.add_widget(self.health_btn)
            
            self.translate_btn = Button(
                text=str(self.t.get("translate_btn", "თარგმანი")),
                on_press=self.run_gemini_translation,
                **font_kwargs
            )
            btn_layout.add_widget(self.translate_btn)

            root.add_widget(btn_layout)

            return root

        except Exception as e:
            err_msg = traceback.format_exc()
            error_root = BoxLayout(orientation='vertical', padding=20)
            error_label = Label(text=f"CRASH:\n{err_msg}", font_size=12, halign="left", valign="top")
            error_label.bind(texture_size=lambda *args: setattr(error_label, 'text_size', error_label.size))
            error_root.add_widget(error_label)
            return error_root

    def update_output(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def test_gemini_status(self, instance):
        self.update_output("მოწმდება კავშირი Google Gemini API-სთან...")
        def task():
            try:
                headers = {"Content-Type": "application/json"}
                payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
                res = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=5)
                if res.status_code == 200:
                    self.update_output("Google Gemini API: კავშირი წარმატებით დამყარდა! ✅ (200 OK)")
                else:
                    self.update_output(f"API შეცდომა: სტატუსი {res.status_code}\n{res.text}")
            except Exception as e:
                self.update_output(f"კავშირის შეცდომა:\n{str(e)}")
        threading.Thread(target=task).start()

    def run_gemini_chat(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        self.update_output(f"იგზავნება Gemini-სთან: {user_text}...")
        
        def task():
            try:
                headers = {"Content-Type": "application/json"}
                payload = {"contents": [{"parts": [{"text": user_text}]}]}
                res = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    reply = data['candidates'][0]['content']['parts'][0]['text']
                    self.update_output(f"Gemini AI პასუხი:\n{reply}")
                else:
                    self.update_output(f"შეცდომა {res.status_code}:\n{res.text}")
            except Exception as e:
                self.update_output(f"შეცდომა:\n{str(e)}")
        threading.Thread(target=task).start()

    def run_gemini_translation(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            user_text = "გამარჯობა"
        self.update_output(f"მიმდინარეობს თარგმნა Gemini-ით...")

        def task():
            try:
                prompt = f"Translate the following text to Georgian and English clearly: {user_text}"
                headers = {"Content-Type": "application/json"}
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                res = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    reply = data['candidates'][0]['content']['parts'][0]['text']
                    self.update_output(f"ნათარგმნი:\n{reply}")
                else:
                    self.update_output(f"შეცდომა {res.status_code}:\n{res.text}")
            except Exception as e:
                self.update_output(f"შეცდომა:\n{str(e)}")
        threading.Thread(target=task).start()

if __name__ == '__main__':
    LingoLensApp().run()
