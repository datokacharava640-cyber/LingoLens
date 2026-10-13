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

# თქვენი ახალი AQ... ფორმატის გასაღები
GEMINI_API_KEY = "AQ.Ab8RN6IdrqqYeI9QvDxue7Euw0kJcc3MRpsehFr1tIUB10vqRQ"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None

TRANSLATIONS = {
    "ka": {
        "code": "ka",
        "name": "ქართული",
        "title": "LingoLens AI — ორმხრივი დიალოგი",
        "ready": "სისტემა მზადაა. დაიწყეთ საუბარი...",
        "send": "გაგზავნა",
        "status_btn": "სტატუსი",
        "reset_btn": "გასუფთავება",
        "placeholder": "ჩაწერეთ ტექსტი...",
        "lang_name": "ქართული (KA)",
        "loading": "მუშავდება..."
    },
    "en": {
        "code": "en",
        "name": "English",
        "title": "LingoLens AI — Live Dialogue",
        "ready": "System ready. Start conversation...",
        "send": "Send",
        "status_btn": "Status",
        "reset_btn": "Reset",
        "placeholder": "Type message...",
        "lang_name": "English (EN)",
        "loading": "Processing..."
    },
    "es": {
        "code": "es",
        "name": "Español",
        "title": "LingoLens AI — Diálogo en Vivo",
        "ready": "Sistema listo...",
        "send": "Enviar",
        "status_btn": "Estado",
        "reset_btn": "Reiniciar",
        "placeholder": "Escribe mensaje...",
        "lang_name": "Español (ES)",
        "loading": "Procesando..."
    },
    "fr": {
        "code": "fr",
        "name": "Français",
        "title": "LingoLens AI — Dialogue en Direct",
        "ready": "Système prêt...",
        "send": "Envoyer",
        "status_btn": "Statut",
        "reset_btn": "Effacer",
        "placeholder": "Tapez message...",
        "lang_name": "Français (FR)",
        "loading": "Traitement..."
    },
    "de": {
        "code": "de",
        "name": "Deutsch",
        "title": "LingoLens AI — Live-Dialog",
        "ready": "System bereit...",
        "send": "Senden",
        "status_btn": "Status",
        "reset_btn": "Zurücksetzen",
        "placeholder": "Nachricht eingeben...",
        "lang_name": "Deutsch (DE)",
        "loading": "In Bearbeitung..."
    },
    "ru": {
        "code": "ru",
        "name": "Русский",
        "title": "LingoLens AI — Живой диалог",
        "ready": "Система готова...",
        "send": "Отправить",
        "status_btn": "Статус",
        "reset_btn": "Сброс",
        "placeholder": "Введите сообщение...",
        "lang_name": "Русский (RU)",
        "loading": "Обработка..."
    }
}

Window.softinput_mode = "below_target"

class ProfessionalLingoLens(App):
    def build(self):
        try:
            self.lang_keys = list(TRANSLATIONS.keys())
            self.lang_idx = 0
            self.t = TRANSLATIONS[self.lang_keys[self.lang_idx]]
            self.chat_history = []
            
            font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}

            root = BoxLayout(orientation='vertical', padding=15, spacing=10)

            self.title_label = Label(
                text=str(self.t["title"]),
                font_size=18,
                bold=True,
                size_hint=(1, 0.08),
                **font_kwargs
            )
            root.add_widget(self.title_label)

            scroll = ScrollView(size_hint=(1, 0.50))
            self.output_label = Label(
                text=str(self.t["ready"]),
                font_size=15,
                halign="left",
                valign="top",
                size_hint_y=None,
                **font_kwargs
            )
            self.output_label.bind(
                width=lambda s, w: setattr(s, 'text_size', (w - 10, None)),
                texture_size=lambda s, t: setattr(s, 'height', max(t[1], 100))
            )
            scroll.add_widget(self.output_label)
            root.add_widget(scroll)

            input_box = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.12))
            self.text_input = TextInput(
                hint_text=str(self.t["placeholder"]),
                multiline=False,
                size_hint=(0.75, 1),
                padding=[10, 10, 10, 10],
                **font_kwargs
            )
            input_box.add_widget(self.text_input)

            self.send_btn = Button(
                text=str(self.t["send"]),
                size_hint=(0.25, 1),
                on_press=self.send_message,
                **font_kwargs
            )
            input_box.add_widget(self.send_btn)
            root.add_widget(input_box)

            controls = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.10))
            self.status_btn = Button(
                text=str(self.t["status_btn"]),
                on_press=self.check_api_status,
                **font_kwargs
            )
            controls.add_widget(self.status_btn)

            self.reset_btn = Button(
                text=str(self.t["reset_btn"]),
                on_press=self.reset_dialogue,
                **font_kwargs
            )
            controls.add_widget(self.reset_btn)
            root.add_widget(controls)

            self.lang_btn = Button(
                text=f"🌐 Language: {self.t['lang_name']}",
                size_hint=(1, 0.10),
                on_press=self.switch_language,
                **font_kwargs
            )
            root.add_widget(self.lang_btn)

            return root

        except Exception:
            err = traceback.format_exc()
            box = BoxLayout(orientation='vertical', padding=10)
            lbl = Label(text=f"Initialization Error:\n{err}", font_size=11)
            box.add_widget(lbl)
            return box

    def get_auth_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GEMINI_API_KEY}",
            "x-goog-api-key": GEMINI_API_KEY
        }

    def update_ui_text(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def switch_language(self, instance):
        self.lang_idx = (self.lang_idx + 1) % len(self.lang_keys)
        self.t = TRANSLATIONS[self.lang_keys[self.lang_idx]]
        
        self.title_label.text = str(self.t["title"])
        self.output_label.text = str(self.t["ready"])
        self.send_btn.text = str(self.t["send"])
        self.status_btn.text = str(self.t["status_btn"])
        self.reset_btn.text = str(self.t["reset_btn"])
        self.text_input.hint_text = str(self.t["placeholder"])
        self.lang_btn.text = f"🌐 Language: {self.t['lang_name']}"
        self.chat_history.clear()

    def reset_dialogue(self, instance):
        self.chat_history.clear()
        self.update_ui_text(self.t["ready"])

    def check_api_status(self, instance):
        self.update_ui_text("Testing connection to Gemini API...")
        def worker():
            try:
                res = requests.post(
                    GEMINI_URL,
                    json={"contents": [{"parts": [{"text": "Ping"}]}]},
                    headers=self.get_auth_headers(),
                    timeout=8
                )
                if res.status_code == 200:
                    self.update_ui_text("API Status: Connected Successfully! ✅")
                else:
                    self.update_ui_text(f"API Connection Failed [{res.status_code}]:\n{res.text[:200]}")
            except Exception as e:
                self.update_ui_text(f"Network Error: {str(e)}")

        threading.Thread(target=worker, daemon=True).start()

    def send_message(self, instance):
        msg = self.text_input.text.strip()
        if not msg:
            return
        
        self.text_input.text = ""
        self.chat_history.append(f"User: {msg}")
        
        context = "\n".join(self.chat_history[-6:])
        target_lang = self.t["name"]
        
        self.update_ui_text(f"⏳ {self.t['loading']}")

        def worker():
            try:
                prompt = (
                    f"You are a professional bilingual assistant facilitating a real-time conversation between a Georgian speaker and a {target_lang} speaker. "
                    f"Provide an accurate response in {target_lang} accompanied by its precise Georgian translation. "
                    f"Maintain perfect grammar and conversational tone.\n\n"
                    f"History:\n{context}\n\nResponse:"
                )
                
                res = requests.post(
                    GEMINI_URL,
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    headers=self.get_auth_headers(),
                    timeout=15
                )

                if res.status_code == 200:
                    data = res.json()
                    ans = data['candidates'][0]['content']['parts'][0]['text']
                    self.chat_history.append(f"AI: {ans}")
                    self.update_ui_text(f"💬 Conversation:\n{ans}")
                else:
                    self.update_ui_text(f"Error {res.status_code}:\n{res.text}")
            except Exception as e:
                self.update_ui_text(f"Request Error: {str(e)}")

        threading.Thread(target=worker, daemon=True).start()

if __name__ == '__main__':
    ProfessionalLingoLens().run()
