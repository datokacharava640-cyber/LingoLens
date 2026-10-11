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

# თქვენი AQ... ფორმატის გასაღები
GEMINI_API_KEY = "AQ.Ab8RN6ICzFuAK7VhU7g6QuunWROFg2gth..."

# მოდელის ბოლო endpoint
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

FONT_PATH = "font.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = None

TRANSLATIONS = {
    "ka": {
        "code": "ka",
        "name": "ქართული",
        "title": "LingoLens AI - ორმხრივი დიალოგი",
        "ready": "დიალოგი მზადაა. დაიწყეთ საუბარი...",
        "send": "გაგზავნა",
        "status_btn": "სტატუსი",
        "reset_btn": "გასუფთავება",
        "placeholder": "დაწერეთ თქვენი რეპლიკა...",
        "lang_name": "ქართული (KA)"
    },
    "en": {
        "code": "en",
        "name": "English",
        "title": "LingoLens AI - Two-Way Dialogue",
        "ready": "Dialogue is ready. Start conversation...",
        "send": "Send",
        "status_btn": "Status",
        "reset_btn": "Reset",
        "placeholder": "Type your message...",
        "lang_name": "English (EN)"
    },
    "es": {
        "code": "es",
        "name": "Español",
        "title": "LingoLens AI - Diálogo Bilateral",
        "ready": "Diálogo listo. Comience...",
        "send": "Enviar",
        "status_btn": "Estado",
        "reset_btn": "Reiniciar",
        "placeholder": "Escribe tu mensaje...",
        "lang_name": "Español (ES)"
    },
    "fr": {
        "code": "fr",
        "name": "Français",
        "title": "LingoLens AI - Dialogue Bidirectionnel",
        "ready": "Dialogue prêt...",
        "send": "Envoyer",
        "status_btn": "Statut",
        "reset_btn": "Effacer",
        "placeholder": "Tapez votre message...",
        "lang_name": "Français (FR)"
    },
    "de": {
        "code": "de",
        "name": "Deutsch",
        "title": "LingoLens AI - Zweiseitiger Dialog",
        "ready": "Dialog bereit...",
        "send": "Senden",
        "status_btn": "Status",
        "reset_btn": "Zurücksetzen",
        "placeholder": "Nachricht eingeben...",
        "lang_name": "Deutsch (DE)"
    },
    "ru": {
        "code": "ru",
        "name": "Русский",
        "title": "LingoLens AI - Двусторонний диалог",
        "ready": "Диалог готов...",
        "send": "Отправить",
        "status_btn": "Статус",
        "reset_btn": "Сброс",
        "placeholder": "Введите сообщение...",
        "lang_name": "Русский (RU)"
    }
}

Window.softinput_mode = "below_target"

class LingoLensApp(App):
    def build(self):
        try:
            self.lang_keys = list(TRANSLATIONS.keys())
            self.current_lang_idx = 0
            self.current_lang_code = self.lang_keys[self.current_lang_idx]
            self.t = TRANSLATIONS[self.current_lang_code]
            self.chat_history = []

            self.font_to_use = FONT_PATH if (FONT_PATH and os.path.exists(FONT_PATH)) else None
            font_kwargs = {'font_name': self.font_to_use} if self.font_to_use else {}

            root = BoxLayout(orientation='vertical', padding=15, spacing=10)
            
            self.title_label = Label(
                text=str(self.t.get("title")),
                font_size=18,
                size_hint=(1, 0.08),
                **font_kwargs
            )
            root.add_widget(self.title_label)
            
            scroll = ScrollView(size_hint=(1, 0.32))
            self.output_label = Label(
                text=str(self.t.get("ready")),
                font_size=14,
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
            
            input_layout = BoxLayout(orientation='horizontal', spacing=5, size_hint=(1, 0.12))
            self.text_input = TextInput(
                text="",
                hint_text=str(self.t.get("placeholder")),
                multiline=False,
                size_hint=(0.75, 1),
                **font_kwargs
            )
            input_layout.add_widget(self.text_input)
            
            self.send_btn = Button(
                text=str(self.t.get("send")),
                size_hint=(0.25, 1),
                on_press=self.run_live_dialogue,
                **font_kwargs
            )
            input_layout.add_widget(self.send_btn)
            root.add_widget(input_layout)
            
            btn_layout = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.12))
            
            self.health_btn = Button(
                text=str(self.t.get("status_btn")),
                on_press=self.test_gemini_status,
                **font_kwargs
            )
            btn_layout.add_widget(self.health_btn)
            
            self.reset_btn = Button(
                text=str(self.t.get("reset_btn")),
                on_press=self.reset_dialogue,
                **font_kwargs
            )
            btn_layout.add_widget(self.reset_btn)

            root.add_widget(btn_layout)

            self.lang_toggle_btn = Button(
                text=f"🌍 Language: {self.t.get('lang_name')}",
                size_hint=(1, 0.10),
                on_press=self.toggle_language,
                **font_kwargs
            )
            root.add_widget(self.lang_toggle_btn)

            return root

        except Exception as e:
            err_msg = traceback.format_exc()
            error_root = BoxLayout(orientation='vertical', padding=20)
            error_label = Label(text=f"CRASH:\n{err_msg}", font_size=12, halign="left", valign="top")
            error_label.bind(texture_size=lambda *args: setattr(error_label, 'text_size', error_label.size))
            error_root.add_widget(error_label)
            return error_root

    def get_headers(self):
        # AQ... გასაღების შემთხვევაში ავტორიზაცია გადაეცემა Bearer ტოკენად ან x-goog-api-key-ით
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GEMINI_API_KEY}",
            "x-goog-api-key": GEMINI_API_KEY
        }

    def toggle_language(self, instance):
        self.current_lang_idx = (self.current_lang_idx + 1) % len(self.lang_keys)
        self.current_lang_code = self.lang_keys[self.current_lang_idx]
        self.t = TRANSLATIONS[self.current_lang_code]

        self.title_label.text = str(self.t.get("title"))
        self.output_label.text = str(self.t.get("ready"))
        self.send_btn.text = str(self.t.get("send"))
        self.health_btn.text = str(self.t.get("status_btn"))
        self.reset_btn.text = str(self.t.get("reset_btn"))
        self.text_input.hint_text = str(self.t.get("placeholder"))
        self.lang_toggle_btn.text = f"🌍 Language: {self.t.get('lang_name')}"
        self.chat_history = []

    def reset_dialogue(self, instance):
        self.chat_history = []
        self.update_output("დიალოგი გასუფთავდა. დაიწყეთ თავიდან...")

    def update_output(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def test_gemini_status(self, instance):
        self.update_output("მოწმდება კავშირი Google Gemini API-სთან...")
        def task():
            try:
                payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
                res = requests.post(
                    f"{GEMINI_URL}?key={GEMINI_API_KEY}", 
                    json=payload, 
                    headers=self.get_headers(), 
                    timeout=7
                )
                if res.status_code == 200:
                    self.update_output("სტატუსი: კავშირი სრულად გამართულია! ✅")
                else:
                    self.update_output(f"შეცდომა {res.status_code}:\n{res.text[:150]}")
            except Exception as e:
                self.update_output(f"შეცდომა: {str(e)}")
        threading.Thread(target=task).start()

    def run_live_dialogue(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        
        target_lang_name = self.t.get("name")
        self.text_input.text = ""
        
        self.chat_history.append(f"User: {user_text}")
        history_str = "\n".join(self.chat_history[-8:])
        
        self.update_output(f"მიმდინარეობს დიალოგი ({target_lang_name})...")

        def task():
            try:
                system_prompt = (
                    f"You are an expert bilingual conversation partner facilitating a flawless, grammatically correct two-way live dialogue between a Georgian speaker and a {target_lang_name} speaker. "
                    f"Ensure absolute grammatical correctness and natural fluency in both Georgian and {target_lang_name}. "
                    f"Respond naturally to the user's latest message, continuing the conversation fluidly. Provide the response both in {target_lang_name} and its accurate Georgian translation/counter-response so both sides can understand each other seamlessly. "
                    f"Conversation history:\n{history_str}\n"
                    f"Format the output clearly and readably."
                )
                
                payload = {"contents": [{"parts": [{"text": system_prompt}]}]}
                res = requests.post(
                    f"{GEMINI_URL}?key={GEMINI_API_KEY}", 
                    json=payload, 
                    headers=self.get_headers(), 
                    timeout=12
                )
                
                if res.status_code == 200:
                    data = res.json()
                    reply = data['candidates'][0]['content']['parts'][0]['text']
                    self.chat_history.append(f"AI: {reply}")
                    self.update_output(f"💬 ორმხრივი დიალოგი:\n{reply}")
                else:
                    self.update_output(f"შეცდომა {res.status_code}:\n{res.text}")
            except Exception as e:
                self.update_output(f"კავშირის შეცდომა:\n{str(e)}")
        threading.Thread(target=task).start()

if __name__ == '__main__':
    LingoLensApp().run()
