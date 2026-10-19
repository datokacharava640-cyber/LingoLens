from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.clock import Clock
import threading
import requests
import os
import base64
import traceback

# Android Native TTS & STT (ხმის ცნობა) pyjnius და plyer-ის მეშვეობით
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Intent = autoclass('android.content.Intent')
    RecognizerIntent = autoclass('android.speech.RecognizerIntent')
    ANDROID_NATIVE_AVAILABLE = True
except Exception:
    ANDROID_NATIVE_AVAILABLE = False

try:
    from plyer import camera, vibrator
    ANDROID_PLYER_AVAILABLE = True
except Exception:
    ANDROID_PLYER_AVAILABLE = False

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else None
SERVER_ENDPOINT = "https://lingo-lens-chi.vercel.app/api/translate"

# მსოფლიოს 100 წამყვანი ენის სრული ლექსიკონი LingoLens AI-სთვის
TRANSLATIONS = {
    "ka": {"name": "ქართული", "title": "✨ LingoLens AI & MicroScope", "hint": "ჩაწერეთ ტექსტი...", "ready": "საიდან დავიწყოთ?"},
    "en": {"name": "English", "title": "✨ LingoLens AI & MicroScope", "hint": "Ask LingoLens...", "ready": "Where should we start?"},
    "es": {"name": "Español", "title": "✨ LingoLens AI & MicroScope", "hint": "Pregunta a LingoLens...", "ready": "¿Por dónde empezamos?"},
    "fr": {"name": "Français", "title": "✨ LingoLens AI & MicroScope", "hint": "Demandez à LingoLens...", "ready": "Par où commencer ?"},
    "de": {"name": "Deutsch", "title": "✨ LingoLens AI & MicroScope", "hint": "Fragen Sie LingoLens...", "ready": "Wo sollen wir anfangen?"},
    "ru": {"name": "Русский", "title": "✨ LingoLens AI & MicroScope", "hint": "Спросите LingoLens...", "ready": "С чего начнем?"},
    "zh": {"name": "中文", "title": "✨ LingoLens AI & MicroScope", "hint": "询问 LingoLens...", "ready": "我们从哪里开始？"},
    "ja": {"name": "日本語", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens에 질문...", "ready": "どこから始めましょうか？"},
    "ar": {"name": "العربية", "title": "✨ LingoLens AI & MicroScope", "hint": "اسأل LingoLens...", "ready": "من أين نبدأ؟"},
    "hi": {"name": "हिन्दी", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens से पूछें...", "ready": "हम कहाँ से शुरू करें?"},
    "pt": {"name": "Português", "title": "✨ LingoLens AI & MicroScope", "hint": "Pergunte ao LingoLens...", "ready": "Por onde começamos?"},
    "it": {"name": "Italiano", "title": "✨ LingoLens AI & MicroScope", "hint": "Chiedi a LingoLens...", "ready": "Da dove iniziamo?"},
    "ko": {"name": "한국어", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens에게 질문하세요...", "ready": "어디부터 시작할까요?"},
    "tr": {"name": "Türkçe", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens'e sorun...", "ready": "Nereden başlayalım?"},
    "uk": {"name": "Українська", "title": "✨ LingoLens AI & MicroScope", "hint": "Спитайте LingoLens...", "ready": "З чого почнемо?"},
    "pl": {"name": "Polski", "title": "✨ LingoLens AI & MicroScope", "hint": "Zapytaj LingoLens...", "ready": "Od czego zaczynamy?"},
    "nl": {"name": "Nederlands", "title": "✨ LingoLens AI & MicroScope", "hint": "Vraag het aan LingoLens...", "ready": "Waar zullen we beginnen?"},
    "vi": {"name": "Tiếng Việt", "title": "✨ LingoLens AI & MicroScope", "hint": "Hỏi LingoLens...", "ready": "Chúng ta bắt đầu từ đâu?"},
    "th": {"name": "ไทย", "title": "✨ LingoLens AI & MicroScope", "hint": "ถาม LingoLens...", "ready": "เราควรเริ่มต้นที่ไหน?"},
    "id": {"name": "Indonesian", "title": "✨ LingoLens AI & MicroScope", "hint": "Tanya LingoLens...", "ready": "Di mana kita mulai?"},
    "ms": {"name": "Melayu", "title": "✨ LingoLens AI & MicroScope", "hint": "Tanya LingoLens...", "ready": "Di mana kita mula?"},
    "fa": {"name": "فارسی", "title": "✨ LingoLens AI & MicroScope", "hint": "از LingoLens بپرسید...", "ready": "از کجا شروع کنیم؟"},
    "ur": {"name": "اردو", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens से پوچھیں...", "ready": "ہم کہاں سے شروع کریں؟"},
    "bn": {"name": "বাংলা", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens-কে জিজ্ঞাসা করুন...", "ready": "আমরা কোথা থেকে শুরু করব?"},
    "el": {"name": "Ελληνικά", "title": "✨ LingoLens AI & MicroScope", "hint": "Ρωτήστε το LingoLens...", "ready": "Πού να ξεκινήσουμε;"},
    "cs": {"name": "Čeština", "title": "✨ LingoLens AI & MicroScope", "hint": "Zeptejte se LingoLens...", "ready": "Kde začít?"},
    "sv": {"name": "Svenska", "title": "✨ LingoLens AI & MicroScope", "hint": "Fråga LingoLens...", "ready": "Var ska vi börja?"},
    "hu": {"name": "Magyar", "title": "✨ LingoLens AI & MicroScope", "hint": "Kérdezd a LingoLens-t...", "ready": "Hol kezdjük?"},
    "ro": {"name": "Română", "title": "✨ LingoLens AI & MicroScope", "hint": "Întreabă LingoLens...", "ready": "De unde începem?"},
    "da": {"name": "Dansk", "title": "✨ LingoLens AI & MicroScope", "hint": "Spørg LingoLens...", "ready": "Hvor skal vi starte?"},
    "fi": {"name": "Suomi", "title": "✨ LingoLens AI & MicroScope", "hint": "Kysy LingoLensiltä...", "ready": "Mistä aloitamן?"},
    "no": {"name": "Norsk", "title": "✨ LingoLens AI & MicroScope", "hint": "Spør LingoLens...", "ready": "Hvor skal vi starte?"},
    "he": {"name": "עברית", "title": "✨ LingoLens AI & MicroScope", "hint": "שאל את LingoLens...", "ready": "איפה נתחיל?"},
    "sw": {"name": "Kiswahili", "title": "✨ LingoLens AI & MicroScope", "hint": "Uliza LingoLens...", "ready": "Tuanze wapi?"},
    "af": {"name": "Afrikaans", "title": "✨ LingoLens AI & MicroScope", "hint": "Vra LingoLens...", "ready": "Waar begin ons?"},
    "sq": {"name": "Shqip", "title": "✨ LingoLens AI & MicroScope", "hint": "Pyet LingoLens...", "ready": "Nga t'ia fillojmë?"},
    "hy": {"name": "Հայերեն", "title": "✨ LingoLens AI & MicroScope", "hint": "Հարցրեք LingoLens-ին...", "ready": "Որտեղից սկսենք:"},
    "az": {"name": "Azərbaycan", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens-dən soruşun...", "ready": "Haradan başlayaq?"},
    "be": {"name": "Беларуская", "title": "✨ LingoLens AI & MicroScope", "hint": "Спытайце LingoLens...", "ready": "З чаго пачнемо?"},
    "bg": {"name": "Български", "title": "✨ LingoLens AI & MicroScope", "hint": "Попитайте LingoLens...", "ready": "Откъде да започнем?"},
    "hr": {"name": "Hrvatski", "title": "✨ LingoLens AI & MicroScope", "hint": "Pitajte LingoLens...", "ready": "Odakle početi?"},
    "et": {"name": "Eesti", "title": "✨ LingoLens AI & MicroScope", "hint": "Küsige LingoLensilt...", "ready": "Kust alustada?"},
    "tl": {"name": "Filipino", "title": "✨ LingoLens AI & MicroScope", "hint": "Magtanong sa LingoLens...", "ready": "Saan tayo magsisimula?"},
    "gl": {"name": "Galego", "title": "✨ LingoLens AI & MicroScope", "hint": "Pregúntalle a LingoLens...", "ready": "Por onde empezamos?"},
    "is": {"name": "Íslenska", "title": "✨ LingoLens AI & MicroScope", "hint": "Spyrðu LingoLens...", "ready": "Hvar eigum við að byrja?"},
    "ga": {"name": "Gaeilge", "title": "✨ LingoLens AI & MicroScope", "hint": "Faigh an freagra ó LingoLens...", "ready": "Cá háit a dtosóimid?"},
    "kk": {"name": "Қазақша", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens-тен сұраңыз...", "ready": "Қայдан бастаймыз?"},
    "lv": {"name": "Latviešu", "title": "✨ LingoLens AI & MicroScope", "hint": "Jautājiet LingoLens...", "ready": "Ar ko sākt?"},
    "lt": {"name": "Lietuvių", "title": "✨ LingoLens AI & MicroScope", "hint": "Paklauskite LingoLens...", "ready": "Nuo ko pradėti?"},
    "mk": {"name": "Македонски", "title": "✨ LingoLens AI & MicroScope", "hint": "Прашај го LingoLens...", "ready": "Од каде да почнеме?"},
    "mt": {"name": "Malti", "title": "✨ LingoLens AI & MicroScope", "hint": "Saqsi lil LingoLens...", "ready": "Minn fejn nibdew?"},
    "mn": {"name": "Монгол", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens-ээс асуу...", "ready": "Хаанаас эхлэх вэ?"},
    "fa": {"name": "فارسی", "title": "✨ LingoLens AI & MicroScope", "hint": "از LingoLens بپرسید...", "ready": "از کجا شروع کنیم؟"},
    "sr": {"name": "Српски", "title": "✨ LingoLens AI & MicroScope", "hint": "Питай LingoLens...", "ready": "Одакле да почнемо?"},
    "sk": {"name": "Slovenčina", "title": "✨ LingoLens AI & MicroScope", "hint": "Opýtajte sa LingoLens...", "ready": "Kde začať?"},
    "sl": {"name": "Slovenščina", "title": "✨ LingoLens AI & MicroScope", "hint": "Vprašajte LingoLens...", "ready": "Kje začeti?"},
    "uz": {"name": "Oʻzbekcha", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLensdan soʻrang...", "ready": "Qayerdan boshlaymiz?"},
    "cy": {"name": "Cymraeg", "title": "✨ LingoLens AI & MicroScope", "hint": "Gofynnwch i LingoLens...", "ready": "Lle dylen ni ddechrau?"},
    "yi": {"name": "ייִדיש", "title": "✨ LingoLens AI & MicroScope", "hint": "פרעגן לינגאָלענס...", "ready": "וואו זאָל מיר אָנהייבן?"},
    "zu": {"name": "isiZulu", "title": "✨ LingoLens AI & MicroScope", "hint": "Buza i-LingoLens...", "ready": "Sizokala kuphi?"},
    "xh": {"name": "isiXhosa", "title": "✨ LingoLens AI & MicroScope", "hint": "Buza uLingoLens...", "ready": "Siza kuqalisa phi?"},
    "yo": {"name": "Yorùbá", "title": "✨ LingoLens AI & MicroScope", "hint": "Bi LingoLens...", "ready": "Nibo ni a ti bẹrẹ?"},
    "ig": {"name": "Igbo", "title": "✨ LingoLens AI & MicroScope", "hint": "Jụọ LingoLens...", "ready": "Olee ebeเรา ga-amalite?"},
    "ha": {"name": "Hausa", "title": "✨ LingoLens AI & MicroScope", "hint": "Tambayi LingoLens...", "ready": "Ina zamu fara?"},
    "am": {"name": "አማርኛ", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens ይጠይቁ...", "ready": "የት እንጀምር?"},
    "ne": {"name": "नेपाली", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens लाई सोध्नुहोस्...", "ready": "हामी कहाँबाट सुरु गरौं?"},
    "si": {"name": "සිංහල", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens වෙතින් විමසන්න...", "ready": "අපි කොහෙන් පටන් ගනිමුද?"},
    "km": {"name": "ខ្មែរ", "title": "✨ LingoLens AI & MicroScope", "hint": "សួរ LingoLens...", "ready": "តើគួរចាប់ផ្តើមពីណា?"},
    "lo": {"name": "ລາວ", "title": "✨ LingoLens AI & MicroScope", "hint": "ຖາມ LingoLens...", "ready": "ພວກເຮົາຄວນເລີ່ມຈາກໃສ?"},
    "my": {"name": "မြန်မာ", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens ကို မေးပါ...", "ready": "ဘယ်ကစရမလဲ?"},
    "ps": {"name": "پښتو", "title": "✨ LingoLens AI & MicroScope", "hint": "د LingoLens څخه وپوښتئ...", "ready": "چیرته پیل وکړو؟"},
    "so": {"name": "Soomaali", "title": "✨ LingoLens AI & MicroScope", "hint": "Weydiiso LingoLens...", "ready": "Halkee baan ka billownaa?"},
    "ku": {"name": "Kurdî", "title": "✨ LingoLens AI & MicroScope", "hint": "Ji LingoLens bipirse...", "ready": "Em ji ku derê dest pê bikin?"},
    "mg": {"name": "Malagasy", "title": "✨ LingoLens AI & MicroScope", "hint": "Manontania an'i LingoLens...", "ready": "Aiza no hanombohana?"},
    "mi": {"name": "Māori", "title": "✨ LingoLens AI & MicroScope", "hint": "Pātai ki a LingoLens...", "ready": "Kei hea e timata ai tatou?"},
    "sm": {"name": "Samoan", "title": "✨ LingoLens AI & MicroScope", "hint": "Fesili ia LingoLens...", "ready": "O fea e tatou te amata ai?"},
    "to": {"name": "Tongan", "title": "✨ LingoLens AI & MicroScope", "hint": "Fekauʻi kia LingoLens...", "ready": "Te tau kamata ki fē?"},
    "fy": {"name": "Frysk", "title": "✨ LingoLens AI & MicroScope", "hint": "Freget LingoLens...", "ready": "Wêr moatte wy begjinne?"},
    "lb": {"name": "Lëtzebuergesch", "title": "✨ LingoLens AI & MicroScope", "hint": "Frot LingoLens...", "ready": "Wou solle mir ufänken?"},
    "gd": {"name": "Gàidhlig", "title": "✨ LingoLens AI & MicroScope", "hint": "Faighnich de LingoLens...", "ready": "Càite an tòisich sinn?"},
    "eo": {"name": "Esperanto", "title": "✨ LingoLens AI & MicroScope", "hint": "Demandu LingoLens...", "ready": "De kie ni komencu?"},
    "la": {"name": "Latina", "title": "✨ LingoLens AI & MicroScope", "hint": "Interroga LingoLens...", "ready": "Unde incipiamus?"},
    "bs": {"name": "Bosanski", "title": "✨ LingoLens AI & MicroScope", "hint": "Pitajte LingoLens...", "ready": "Odakle da počnemo?"},
    "ny": {"name": "Chichewa", "title": "✨ LingoLens AI & MicroScope", "hint": "Funsani LingoLens...", "ready": "Kodi tiyambire pati?"},
    "st": {"name": "Sesotho", "title": "✨ LingoLens AI & MicroScope", "hint": "Botsa LingoLens...", "ready": "Re qala ka kae?"},
    "sn": {"name": "Shona", "title": "✨ LingoLens AI & MicroScope", "hint": "Bvunza LingoLens...", "ready": "Tinotangira kupi?"},
    "ug": {"name": "Uyghur", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens دين سورەڭ...", "ready": "قەيەردىن باشلايمىز؟"},
    "tt": {"name": "Tatar", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens-тан сора...", "ready": "Каян башлыйбыз?"},
    "tk": {"name": "Türkmen", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLens-den soräň...", "ready": "Nireden başlamaly?"},
    "uz": {"name": "Oʻzbek", "title": "✨ LingoLens AI & MicroScope", "hint": "LingoLensdan soʻrang...", "ready": "Qayerdan boshlaymiz?"},
    "jv": {"name": "Javanese", "title": "✨ LingoLens AI & MicroScope", "hint": "Takon LingoLens...", "ready": "Saka ngendi miwiti?"},
    "su": {"name": "Sundanese", "title": "✨ LingoLens AI & MicroScope", "hint": "Tanya LingoLens...", "ready": "Ti mana urang mimitian?"},
    "ceb": {"name": "Cebuano", "title": "✨ LingoLens AI & MicroScope", "hint": "Pangutana sa LingoLens...", "ready": "Asa kita magsugod?"},
    "hmn": {"name": "Hmong", "title": "✨ LingoLens AI & MicroScope", "hint": "Nug LingoLens...", "ready": "Peb pib qhov twg?"},
    "co": {"name": "Corsican", "title": "✨ LingoLens AI & MicroScope", "hint": "Dumandate à LingoLens...", "ready": "Ond'è chì cumicinimu?"},
    "sm": {"name": "Samoan", "title": "✨ LingoLens AI & MicroScope", "hint": "Fesili ia LingoLens...", "ready": "O fea e amata ai?"}
}

Window.clearcolor = (0.07, 0.09, 0.12, 1)
Window.softinput_mode = "below_target"


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        try:
            self.lang_keys = list(TRANSLATIONS.keys())
            self.lang_idx = 0
            self.t = TRANSLATIONS[self.lang_keys[self.lang_idx]]
            self.chat_history = []
            self.tts = None
            self.last_ai_text = ""

            if ANDROID_NATIVE_AVAILABLE:
                try:
                    activity = PythonActivity.mActivity
                    self.tts = TextToSpeech(activity, None)
                except Exception as e:
                    print("TTS Init Error:", e)

            font_kwargs = {'font_name': FONT_PATH} if FONT_PATH else {}

            root = BoxLayout(orientation='vertical', padding=14, spacing=10)

            top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), spacing=6)
            self.title_label = Label(
                text=str(self.t["title"]), font_size=15, bold=True, 
                halign="left", color=(0.9, 0.95, 1, 1), **font_kwargs
            )
            top_layout.add_widget(self.title_label)

            self.voice_nav_btn = Button(
                text="✈️ ხმა", size_hint=(None, 1), width=75,
                background_color=(0.2, 0.7, 0.4, 1), color=(1, 1, 1, 1),
                on_press=lambda x: setattr(self.manager, 'current', 'voice_translator'), **font_kwargs
            )
            top_layout.add_widget(self.voice_nav_btn)

            self.lang_btn = Button(
                text=f"🌐 {self.t['name']}", size_hint=(None, 1), width=105,
                background_color=(0.15, 0.2, 0.3, 1), color=(1, 1, 1, 1),
                on_press=self.switch_language, **font_kwargs
            )
            top_layout.add_widget(self.lang_btn)
            root.add_widget(top_layout)

            scroll = ScrollView(size_hint=(1, 0.58), bar_width=4)
            self.output_label = Label(
                text=str(self.t["ready"]), font_size=15, halign="left", valign="top", 
                size_hint_y=None, color=(0.85, 0.9, 0.95, 1), **font_kwargs
            )
            self.output_label.bind(
                width=lambda s, w: setattr(s, 'text_size', (w - 15, None)),
                texture_size=lambda s, t: setattr(s, 'height', max(t[1], 150))
            )
            scroll.add_widget(self.output_label)
            root.add_widget(scroll)

            input_container = BoxLayout(orientation='vertical', spacing=6, size_hint=(1, 0.28))
            
            self.text_input = TextInput(
                hint_text=self.t["hint"], multiline=False, size_hint=(1, 0.4),
                padding=[10, 10, 10, 10], background_color=(0.13, 0.17, 0.24, 1),
                foreground_color=(1, 1, 1, 1), hint_text_color=(0.5, 0.55, 0.65, 1), **font_kwargs
            )
            input_container.add_widget(self.text_input)

            bottom_actions = BoxLayout(orientation='horizontal', spacing=6, size_hint=(1, 0.6))
            
            self.send_btn = Button(
                text="🚀 გაგზავნა", size_hint=(0.25, 1),
                background_color=(0.2, 0.5, 0.9, 1), color=(1, 1, 1, 1),
                on_press=self.send_message, **font_kwargs
            )
            bottom_actions.add_widget(self.send_btn)

            self.stt_btn = Button(
                text="🎙️ აგენტი", size_hint=(0.25, 1),
                background_color=(0.8, 0.3, 0.2, 1), color=(1, 1, 1, 1),
                on_press=self.start_voice_agent, **font_kwargs
            )
            bottom_actions.add_widget(self.stt_btn)

            self.microscope_btn = Button(
                text="🔬 მიკროსკოპი", size_hint=(0.28, 1),
                background_color=(0.1, 0.6, 0.4, 1), color=(1, 1, 1, 1),
                on_press=self.analyze_microscope_image, **font_kwargs
            )
            bottom_actions.add_widget(self.microscope_btn)

            self.speak_btn = Button(
                text="🔊 აუდიო", size_hint=(0.22, 1),
                background_color=(0.15, 0.2, 0.3, 1), color=(1, 1, 1, 1),
                on_press=self.speak_response, **font_kwargs
            )
            bottom_actions.add_widget(self.speak_btn)

            input_container.add_widget(bottom_actions)
            root.add_widget(input_container)

            self.add_widget(root)

        except Exception:
            err = traceback.format_exc()
            box = BoxLayout(orientation='vertical', padding=10)
            box.add_widget(Label(text=f"App Error:\n{err}", font_size=11))
            self.add_widget(box)

    def update_ui(self, text):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', str(text)))

    def speak_text(self, text):
        if ANDROID_NATIVE_AVAILABLE and self.tts:
            try:
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print("TTS Error:", e)

    def start_voice_agent(self, instance):
        if ANDROID_NATIVE_AVAILABLE:
            try:
                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "გთხოვთ, ისაუბრეთ...")
                activity = PythonActivity.mActivity
                activity.startActivityForResult(intent, 100)
            except Exception as e:
                self.update_ui(f"ხმის ცნობის შეცდომა: {str(e)}")
        else:
            self.update_ui("⚠️ Android Native Voice-to-Text არ არის ხელმისაწვდომი ამ მოწყობილობაზე.")

    def speak_response(self, instance):
        if self.last_ai_text:
            self.speak_text(self.last_ai_text)

    def switch_language(self, instance):
        self.lang_idx = (self.lang_idx + 1) % len(self.lang_keys)
        self.t = TRANSLATIONS[self.lang_keys[self.lang_idx]]
        self.title_label.text = str(self.t["title"])
        self.lang_btn.text = f"🌐 {self.t['name']}"
        self.text_input.hint_text = self.t["hint"]

    def send_message(self, instance):
        msg = self.text_input.text.strip()
        if not msg:
            return

        self.text_input.text = ""
        target_lang = self.t["name"]
        self.chat_history.append(f"User: {msg}")
        self.update_ui("⏳ Gemini AI ფიქრობს...")

        def worker():
            try:
                payload = {
                    "message": msg,
                    "target_lang": target_lang,
                    "history": self.chat_history[-4:]
                }
                res = requests.post(SERVER_ENDPOINT, json=payload, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    ai_res = data.get("response", "")
                    self.last_ai_text = ai_res
                    self.chat_history.append(f"AI: {ai_res}")
                    self.update_ui("\n\n".join(self.chat_history[-6:]))
                    self.speak_text(ai_res)
                else:
                    self.update_ui(f"სერვერის შეცდომა [{res.status_code}]")
            except Exception as e:
                self.update_ui(f"ქსელის შეცდომა: {str(e)}")

        threading.Thread(target=worker, daemon=True).start()

    def analyze_microscope_image(self, instance):
        img_path = "microscope_capture.jpg"
        if not os.path.exists(img_path):
            img_path = "sample.jpg"

        if not os.path.exists(img_path):
            self.update_ui("⚠️ ფოტო ვერ მოიძებნა (microscope_capture.jpg).")
            return

        self.update_ui("🔬 მიკროსკოპული ფოტოს ანალიზი Gemini AI-ს მეშვეობით...")

        def image_worker():
            try:
                with open(img_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

                payload = {
                    "image_base64": encoded_string,
                    "message": "გააანალიზე ეს მიკროსკოპული გამოსახულება დეტალურად.",
                    "target_lang": self.t["name"]
                }
                res = requests.post(SERVER_ENDPOINT, json=payload, timeout=20)
                if res.status_code == 200:
                    data = res.json()
                    ai_res = data.get("response", "")
                    self.last_ai_text = ai_res
                    self.chat_history.append(f"🔬 AI MicroScope: {ai_res}")
                    self.update_ui("\n\n".join(self.chat_history[-6:]))
                    self.speak_text(ai_res)
                else:
                    self.update_ui(f"შეცდომა სერვერზე [{res.status_code}]")
            except Exception as e:
                self.update_ui(f"ფოტოს დამუშავების შეცდომა: {str(e)}")

        threading.Thread(target=image_worker, daemon=True).start()


class VoiceTranslatorScreen(Screen):
    def __init__(self, **kwargs):
        super(VoiceTranslatorScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        title = Label(text="[b]LingoLens Voice Translator[/b]", markup=True, font_size='22sp', size_hint_y=None, height=50)
        layout.add_widget(title)

        back_btn = Button(text="⬅️ მთავარ მენიუში დაბრუნება", size_hint_y=None, height=50, background_color=(0.3, 0.3, 0.3, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)


class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(VoiceTranslatorScreen(name='voice_translator'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()
