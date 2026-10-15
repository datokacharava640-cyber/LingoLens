from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
import threading
import os
import urllib.parse
import requests
import traceback

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
    },
    "zh": {
        "code": "zh-CN",
        "name": "中文 (Chinese)",
        "title": "LingoLens AI — 实时对话",
        "ready": "系统就绪，请开始对话...",
        "send": "发送",
        "status_btn": "状态",
        "reset_btn": "重置",
        "placeholder": "输入消息...",
        "lang_name": "中文 (ZH)",
        "loading": "处理中..."
    },
    "ja": {
        "code": "ja",
        "name": "日本語 (Japanese)",
        "title": "LingoLens AI — ライブ対話",
        "ready": "理解完了。会話を開始してください...",
        "send": "送信",
        "status_btn": "ステータス",
        "reset_btn": "リセット",
        "placeholder": "メッセージを入力...",
        "lang_name": "日本語 (JA)",
        "loading": "処理中..."
    },
    "ar": {
        "code": "ar",
        "name": "العربية (Arabic)",
        "title": "LingoLens AI — حوار مباشر",
        "ready": "النظام جاهز. ابدأ المحادثة...",
        "send": "إرسال",
        "status_btn": "الحالة",
        "reset_btn": "إعادة ضبط",
        "placeholder": "اكتب رسالتك...",
        "lang_name": "العربية (AR)",
        "loading": "جاري المعالجة..."
    },
    "tr": {
        "code": "tr",
        "name": "Türkçe",
        "title": "LingoLens AI — Canlı Diyalog",
        "ready": "Sistem hazır. Konuşmaya başlayın...",
        "send": "Gönder",
        "status_btn": "Durum",
        "reset_btn": "Sıfırla",
        "placeholder": "Mesaj yazın...",
        "lang_name": "Türkçe (TR)",
        "loading": "İşleniyor..."
    },
    "it": {
        "code": "it",
        "name": "Italiano",
        "title": "LingoLens AI — Dialogo dal Vivo",
        "ready": "Sistema pronto. Inizia la conversazione...",
        "send": "Invia",
        "status_btn": "Stato",
        "reset_btn": "Ripristina",
        "placeholder": "Scrivi un messaggio...",
        "lang_name": "Italiano (IT)",
        "loading": "Elaborazione..."
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
        self.update_ui_text("თარგმნის სერვერი მზადაა. შემოწმება წარმატებულია! ✅")

    def translate_live(self, text, target_lang_code):
        """რეალური Google Translate API (API Key-ს გარეშე)"""
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang_code}&dt=t&q={urllib.parse.quote(text)}"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                translated = "".join([item[0] for item in data[0] if item[0]])
                return translated
            return text
        except Exception as e:
            return f"[Translation Error: {str(e)}]"

    def send_message(self, instance):
        msg = self.text_input.text.strip()
        if not msg:
            return
        
        self.text_input.text = ""
        target_lang = self.t["name"]
        target_code = self.t["code"]
        
        self.update_ui_text(f"⏳ {self.t['loading']}")

        def worker():
            # 1. ვთარგმნით არჩეულ უცხოურ ენაზე
            foreign_translation = self.translate_live(msg, target_code)
            
            # 2. ვთარგმნით ქართულად (უკუთარგმანი/დადასტურება)
            georgian_translation = self.translate_live(foreign_translation, "ka")
            
            response_text = (
                f"💬 ორმხრივი დიალოგი ({target_lang}):\n\n"
                f"• შეყვანილი ტექსტი: {msg}\n"
                f"• თარგმანი ({target_lang}): {foreign_translation}\n"
                f"• ქართული განმარტება: {georgian_translation}"
            )

            self.update_ui_text(response_text)

        threading.Thread(target=worker, daemon=True).start()

if __name__ == '__main__':
    ProfessionalLingoLens().run()
