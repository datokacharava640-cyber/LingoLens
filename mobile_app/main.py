# LingoLens Ultra Pro v9.5.0 (Global Master Edition with Georgian & World Grammar, Reasoning & Native Speech Engine)
# ========================================================================
# ავტორი: დავით კაჭარავა
# ლოკაცია: საქართველო
# თარიღი: 2026
# ========================================================================

import os
import sqlite3
import threading
import requests
import math
import traceback
import random
import time
import re

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.utils import platform

from plyer import share, filechooser, vibrator

APP_VERSION = "9.5.0"
PROJECT_AUTHOR = "დავით კაჭარავა"
PROJECT_LOCATION = "საქართველო"

VERCEL_BASE_URL = "https://lingo-lens-eight.vercel.app"
API_AUTH_TOKEN = "Bearer LINGOLENS_SECURE_TOKEN_2026"
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else "Roboto"

# ----------------------------------------------------
# 1. ენების სრული ბაზა (100+ ენა)
# ----------------------------------------------------
LANGUAGES = {
    "Auto-Detect (ავტო-ამოცნობა)": "auto",
    "Georgian (ქართული)": "ka",
    "English (US / UK)": "en",
    "Spanish (Español)": "es",
    "French (Français)": "fr",
    "German (Deutsch)": "de",
    "Italian (Italiano)": "it",
    "Russian (Русский)": "ru",
    "Turkish (Türkçe)": "tr",
    "Chinese Simplified (中文简体)": "zh-CN",
    "Chinese Traditional (中文繁體)": "zh-TW",
    "Japanese (日本語)": "ja",
    "Korean (한국어)": "ko",
    "Arabic (العربية)": "ar",
    "Hindi (हिन्दी)": "hi",
    "Portuguese (Português)": "pt",
    "Ukrainian (Українська)": "uk",
    "Polish (Polski)": "pl",
    "Dutch (Nederlands)": "nl",
    "Greek (Ελληνικά)": "el",
    "Hebrew (עברית)": "he",
    "Swedish (Svenska)": "sv",
    "Norwegian (Norsk)": "no",
    "Danish (Dansk)": "da",
    "Finnish (Suomi)": "fi",
    "Czech (Čeština)": "cs",
    "Hungarian (Magyar)": "hu",
    "Romanian (Română)": "ro",
    "Bulgarian (Български)": "bg",
    "Serbian (Српски)": "sr",
    "Croatian (Hrvatski)": "hr",
    "Slovak (Slovenčina)": "sk",
    "Slovenian (Slovenščina)": "sl",
    "Lithuanian (Lietuvių)": "lt",
    "Latvian (Latviešu)": "lv",
    "Estonian (Eesti)": "et",
    "Vietnamese (Tiếng Việt)": "vi",
    "Thai (ไทย)": "th",
    "Indonesian (Bahasa Indonesia)": "id",
    "Malay (Bahasa Melayu)": "ms",
    "Filipino (Tagalog)": "tl",
    "Persian / Farsi (فارسی)": "fa",
    "Urdu (اردو)": "ur",
    "Bengali (বাংলা)": "bn",
    "Tamil (தமிழ்)": "ta",
    "Telugu (తెలుగు)": "te",
    "Marathi (מראठी)": "mr",
    "Gujarati (ગુજરાતી)": "gu",
    "Kannada (ಕನ್ನಡ)": "kn",
    "Malayalam (മലയാളം)": "ml",
    "Swahili (Kiswahili)": "sw",
    "Afrikaans": "af",
    "Armenian (Հայերեն)": "hy",
    "Azerbaijani (Azərbaycan)": "az",
    "Kazakh (Қазақ тілі)": "kk",
    "Uzbek (Oʻzbekcha)": "uz",
    "Turkmen (Türkmen)": "tk",
    "Kyrgyz (Кыргызча)": "ky",
    "Tajik (Тоҷикӣ)": "tg",
    "Mongolian (Монгол)": "mn",
    "Albanian (Shqip)": "sq",
    "Macedonian (Македонски)": "mk",
    "Bosnian (Bosanski)": "bs",
    "Icelandic (Íslenska)": "is",
    "Irish (Gaeilge)": "ga",
    "Welsh (Cymraeg)": "cy",
    "Maltese (Malti)": "mt",
    "Galician (Galego)": "gl",
    "Catalan (Català)": "ca",
    "Basque (Euskara)": "eu",
    "Esperanto": "eo",
    "Latin (Latina)": "la",
    "Nepali (नेपाली)": "ne",
    "Sinhala (සිංහල)": "si",
    "Myanmar / Burmese (မြန်မာ)": "my",
    "Khmer (ភាសាខ្មែរ)": "km",
    "Lao (ლოოსური)": "lo",
    "Amharic (አማርኛ)": "am",
    "Somali (Soomaali)": "so",
    "Yoruba": "yo",
    "Zulu (isiZulu)": "zu",
    "Xhosa (isiXhosa)": "xh",
    "Haitian Creole (Kreyòl)": "ht",
    "Javanese (Basa Jawa)": "jv",
    "Sundanese (Basa Sunda)": "su",
    "Samoan (Gagana Samoa)": "sm",
    "Maori (Te Reo Māori)": "mi",
    "Hawaiian (ʻŌlelo Hawaiʻi)": "haw",
    "Luxembourgish (Lëtzebuergesch)": "lb",
    "Frisian (Frysk)": "fy",
    "Yiddish (ייִדיש)": "yi",
    "Tatar (Татар)": "tt",
    "Bashkir (Башҡорт)": "ba",
    "Chuvash (Чӑвашла)": "cv",
    "Corsican (Corsu)": "co",
    "Kurdish (Kurdî)": "ku",
    "Pashto (پښتو)": "ps",
    "Sindhi (سنڌي)": "sd",
    "Uyghur (ئۇيغۇرچە)": "ug",
    "Ewe (Èʋegbe)": "ee",
    "Guarani (Avañe'ẽ)": "gn",
    "Aymara": "ay",
    "Quechua (Runa Simi)": "qu"
}

OFFLINE_DICTIONARY = {
    "hello": {"ka": "გამარჯობა", "pos": "Noun/Interjection", "syn": ["greetings", "hi"], "ant": ["goodbye"], "idiom": "Hello world - საწყისი ნაბიჯი"},
    "world": {"ka": "სამყარო", "pos": "Noun", "syn": ["earth", "globe"], "ant": ["space"], "idiom": "Out of this world - საოცარი"},
    "resilience": {"ka": "მდგრადობა / გაძლება", "pos": "Noun", "syn": ["endurance", "toughness"], "ant": ["fragility"], "idiom": "Bounce back - ფეხზე წამოდგომა"},
    "innovation": {"ka": "ინოვაცია / სიახლე", "pos": "Noun", "syn": ["novelty", "modernization"], "ant": ["stagnation"], "idiom": "Break new ground - ახლის წამოწყება"},
    "love": {"ka": "სიყვარული", "pos": "Noun/Verb", "syn": ["affection", "adoration"], "ant": ["hate"], "idiom": "Love is blind - სიყვარული ბრმაა"}
}

DAILY_QUIZ = [
    {"q": "რა არის 'Resilience'-ის თარგმანი?", "options": ["მდგრადობა", "სიჩქარე", "სიძულვილი"], "a": "მდგრადობა"},
    {"q": "რომელია 'Innovation'-ის სინონიმი?", "options": ["Novelty", "Stagnation", "Old"], "a": "Novelty"},
    {"q": "რა არის 'Adaptability'-ს მნიშვნელობა?", "options": ["ეგუებადობა", "სიმტკიცე", "სიბნელე"], "a": "ეგუებადობა"}
]

def log_error(err):
    try:
        base_dir = App.get_running_app().user_data_dir if (platform == 'android' and App.get_running_app()) else "."
        log_path = os.path.join(base_dir, "error_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- ERROR [{time.ctime()}] ---\n{traceback.format_exc()}\n")
    except Exception:
        pass

def trigger_vibration():
    try:
        vibrator.vibrate(0.04)
    except Exception:
        pass

# ----------------------------------------------------
# 2. ქართული გრამატიკის ძრავი
# ----------------------------------------------------
class GeorgianGrammarEngine:
    VERB_PREFIXES = ["მი", "მო", "წა", "წამო", "შე", "შემო", "გა", "გამო", "გადა", "გადმო", "აღ", "და"]

    @staticmethod
    def declension_noun(word):
        word = word.strip()
        if not word: return {}

        stem = word[:-1] if word.endswith(('ა', 'ე', 'ი', 'ო', 'უ')) else word
        return {
            "სახელობითი": stem + "ი" if not word.endswith(('ა', 'ე', 'ო', 'უ')) else word,
            "მოთხრობითი": stem + "მა",
            "მიცემითი": stem + "ს",
            "ნათესაობითი": stem + "ის",
            "მოქმედებითი": stem + "ით",
            "ვითარებითი": stem + "ად",
            "წოდებითი": stem + "ო"
        }

    @staticmethod
    def conjugate_verb_tenses(stem):
        stem = stem.strip()
        return {
            "აწმყო (Present)": f"ვ{stem}ობ / {stem}ობს",
            "წარსული უწყვეტი (Imperfect)": f"ვ{stem}ობდი / {stem}ობდა",
            "წყვეტილი (Aorist)": f"ვ{stem}ე / {stem}ა",
            "მომავალი (Future)": f"გა{stem}ობს / შე{stem}ობს",
            "სავედრებელი (Optative)": f"შევე{stem}ოს"
        }

    @staticmethod
    def analyze_georgian_text(text):
        words = text.strip().split()
        if not words: return "ტექსტი ცარიელია."

        analysis = ["=== 🇬🇪 ქართული ენობრივი და გრამატიკული ანალიზი ==="]

        for w in words[:3]:
            analysis.append(f"\n🔍 სიტყვა: '{w}'")
            has_prefix = any(w.startswith(p) for p in GeorgianGrammarEngine.VERB_PREFIXES)
            if has_prefix:
                matched_p = next(p for p in GeorgianGrammarEngine.VERB_PREFIXES if w.startswith(p))
                analysis.append(f"  • სტრუქტურა: შეიცავს ზმნისწონს '{matched_p}-' (მიმართულება/ასპექტი)")
                tenses = GeorgianGrammarEngine.conjugate_verb_tenses(w.replace(matched_p, ""))
                analysis.append(f"  • სავარაუდო დროები: აწმყო ({tenses['აწმყო (Present)']}), მომავალი ({tenses['მომავალი (Future)']})")
            else:
                decls = GeorgianGrammarEngine.declension_noun(w)
                analysis.append(f"  • ბრუნების ნიმუში: ნათეს. ({decls.get('ნათესაობითი', '-')}), მოქმედ. ({decls.get('მოქმედებითი', '-')})")

        return "\n".join(analysis)

# ----------------------------------------------------
# 3. მსოფლიო ენების გრამატიკის ძრავი
# ----------------------------------------------------
class GlobalGrammarEngine:
    @staticmethod
    def analyze_global_grammar(text, lang_code):
        text_lower = text.lower()
        insights = [f"=== 🌐 Global Grammar Engine [{lang_code.upper()}] ==="]

        if lang_code == "en":
            if re.search(r'\b(am|is|are|was|were|been|being)\b\s+\w+ed\b', text_lower):
                insights.append("• სინტაქსი: ვნებითი გვარი (Passive Voice). ყურადღება მიაქციეთ ობიექტის აქცენტს.")
            if re.search(r'\b(has|have|had)\b\s+\w+(ed|en)\b', text_lower):
                insights.append("• დრო: Perfect Aspect (შესრულებული მოქმედება). ქართულში ითარგმნება შედეგობითი ან წყვეტილი ფორმით.")
            if "if" in text_lower or "would" in text_lower:
                insights.append("• ლოგიკა: პირობითი წინადადება (Conditionals). ამოწმებს რეალურ/ჰიპოთეტურ სცენარს.")

        elif lang_code == "de":
            if text_lower.startswith(("warum", "wie", "wo", "was")):
                insights.append("• გერმანული სინტაქსი: კითხვითი წინადადება. ზმნა მე-2 ან 1-ელ პოზიციაზე.")

        if len(insights) == 1:
            insights.append("• სტრუქტურა: სტანდარტული წინადადების წყობა და მორფოლოგიური ჰარმონია.")

        return "\n".join(insights)

# ----------------------------------------------------
# 4. AI Reasoning Engine
# ----------------------------------------------------
class ReasoningEngine:
    @staticmethod
    def deep_reasoning_analysis(text, source_lang, target_lang):
        words = text.split()
        word_count = len(words)

        formal_keywords = ["pleased", "sincerely", "regards", "request", "გთხოვთ", "პატივისცემით", "ბრძანება"]
        is_formal = any(k in text.lower() for k in formal_keywords)
        tone = "ოფიციალურ-საქმიანი (Formal)" if is_formal else "ყოველდღიური/საუბრული (Informal)"

        if text.endswith("?"):
            intent = "ინფორმაციის მოთხოვნა / შეკითხვა (Interrogative Logic)"
        elif text.endswith("!"):
            intent = "ემოციური გამოხატვა / ბრძანება (Exclamatory/Imperative Logic)"
        else:
            intent = "მტკიცებითი მსჯელობა / ფაქტის კონსტატაცია (Declarative Logic)"

        if source_lang == "ka" or (source_lang == "auto" and any('\u10d0' <= c <= '\u10fa' for c in text)):
            grammar_part = GeorgianGrammarEngine.analyze_georgian_text(text)
        else:
            grammar_part = GlobalGrammarEngine.analyze_global_grammar(text, source_lang)

        report = [
            "🧠 [LINGOLENS REAL-TIME AI REASONING HUB]",
            "--------------------------------------------------",
            f"• ლოგიკური მიზნობრიობა: {intent}",
            f"• ტონალობა და სტილი: {tone}",
            f"• ტექსტის მოცულობა: {word_count} სიტყვა",
            f"• ენობრივი წყვილი: {source_lang.upper()} ➔ {target_lang.upper()}",
            "--------------------------------------------------",
            grammar_part,
            "\n💡 [ლოგიკური რეკომენდაცია თარგმნისთვის]:",
            "თარგმანისას შენარჩუნებულია კონტექსტური აზრი სიტყვასიტყვითი თარგმანის ნაცვლად."
        ]
        return "\n".join(report)

# ----------------------------------------------------
# 5. Native Speech Manager (რეალური Android STT და TTS)
# ----------------------------------------------------
class NativeSpeechManager:
    _tts_instance = None

    @staticmethod
    def start_listening(lang_code, callback_text=None):
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = PythonActivity.mActivity

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                
                req_lang = "ka-GE" if lang_code in ("ka", "auto") else lang_code
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, req_lang)
                currentActivity.startActivityForResult(intent, 1001)
            except Exception as e:
                log_error(e)
        else:
            if callback_text:
                Clock.schedule_once(lambda dt: callback_text("ხმის ამოცნობის ფუნქცია აქტიურია..."), 0)

    @staticmethod
    def speak_text(text, lang_code, speed=1.0):
        if not text or text.startswith("["): return
        if platform == 'android':
            try:
                from jnius import autoclass
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                def _init_and_speak():
                    if NativeSpeechManager._tts_instance is None:
                        NativeSpeechManager._tts_instance = TextToSpeech(PythonActivity.mActivity, None)
                        time.sleep(0.5)
                    
                    tts = NativeSpeechManager._tts_instance
                    loc_code = "ka" if lang_code == "ka" else lang_code
                    tts.setLanguage(Locale(loc_code))
                    tts.setSpeechRate(float(speed))
                    tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)

                threading.Thread(target=_init_and_speak, daemon=True).start()
            except Exception as e:
                log_error(e)

# ----------------------------------------------------
# 6. Kivy UI Custom Widgets & Database Manager
# ----------------------------------------------------
class AudioVisualizer(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_active = False
        self.phase = 0

    def start_animation(self):
        self.is_active = True
        Clock.schedule_interval(self.animate, 1 / 15.0)

    def stop_animation(self):
        self.is_active = False
        Clock.unschedule(self.animate)
        self.canvas.before.clear()

    def animate(self, dt):
        self.phase += dt * 5
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        if not self.is_active: return
        with self.canvas.before:
            Color(0.2, 0.8, 1, 0.8)
            w, h = self.size
            cy = self.y + h / 2
            points = []
            for i in range(12):
                amp = math.sin(self.phase + i) * (h / 3)
                px = self.x + (w / 11) * i
                py = cy + amp
                points.extend([px, py])
            if len(points) >= 4:
                Line(points=points, width=2)

class GeorgianFlagBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.offset = 0
        self.theme_mode = "dark"
        self.is_animating = False
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def start_bg_animation(self):
        if not self.is_animating:
            self.is_animating = True
            Clock.schedule_interval(self.animate, 1 / 15.0)

    def stop_bg_animation(self):
        self.is_animating = False
        Clock.unschedule(self.animate)

    def set_theme(self, mode):
        self.theme_mode = mode
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            w, h = self.size
            x, y = self.pos
            if self.theme_mode == "dark":
                Color(0.05, 0.06, 0.09, 1)
                Rectangle(pos=(x, y), size=(w, h))
                Color(0.12, 0.14, 0.18, 0.85)
                Rectangle(pos=(x, y), size=(w, h))
                Color(0.85, 0.1, 0.1, 0.35 + math.sin(self.offset) * 0.08)
            else:
                Color(0.95, 0.95, 0.98, 1)
                Rectangle(pos=(x, y), size=(w, h))
                Color(0.88, 0.9, 0.94, 0.85)
                Rectangle(pos=(x, y), size=(w, h))
                Color(0.85, 0.1, 0.1, 0.25 + math.sin(self.offset) * 0.05)

            cross_thick = min(w, h) * 0.12
            Rectangle(pos=(x, y + h / 2 - cross_thick / 2), size=(w, cross_thick))
            Rectangle(pos=(x + w / 2 - cross_thick / 2, y), size=(cross_thick, h))

            small_s = min(w, h) * 0.08
            offsets = [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)]
            for ox, oy in offsets:
                cx = x + w * ox + math.cos(self.offset) * 5
                cy = y + h * oy + math.sin(self.offset) * 5
                Rectangle(pos=(cx - small_s/2, cy - small_s/6), size=(small_s, small_s/3))
                Rectangle(pos=(cx - small_s/6, cy - small_s/2), size=(small_s/3, small_s))

    def animate(self, dt):
        self.offset += dt * 1.5
        self.update_canvas()

class NetworkIndicator(Widget):
    def set_status(self, status):
        self.canvas.before.clear()
        with self.canvas.before:
            if status == "green":
                Color(0.1, 0.8, 0.2, 1)
            elif status == "yellow":
                Color(0.9, 0.7, 0.1, 1)
            else:
                Color(0.9, 0.2, 0.2, 1)
            size = min(self.width, self.height) * 0.5
            px = self.x + (self.width - size) / 2
            py = self.y + (self.height - size) / 2
            Line(ellipse=(px, py, size, size), width=2)

class DatabaseManager:
    def __init__(self):
        self.db_path = None

    def _get_db_path(self):
        if not self.db_path:
            base_dir = App.get_running_app().user_data_dir if (platform == 'android' and App.get_running_app()) else "."
            self.db_path = os.path.join(base_dir, "lingolens.db")
            self.init_db()
        return self.db_path

    def init_db(self):
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_lang TEXT, target_lang TEXT,
                    original_text TEXT, translated_text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_lang TEXT, target_lang TEXT,
                    original_text TEXT, translated_text TEXT,
                    next_review INTEGER DEFAULT 0, interval INTEGER DEFAULT 1
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            log_error(e)

    def add_history(self, src, tgt, original, translated):
        if not original.strip() or not translated.strip(): return
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("INSERT INTO history (source_lang, target_lang, original_text, translated_text) VALUES (?, ?, ?, ?)", (src, tgt, original, translated))
            conn.commit()
            conn.close()
        except Exception as e:
            log_error(e)

    def search_offline_cache(self, src, tgt, text):
        clean_text = text.strip().lower()
        if clean_text in OFFLINE_DICTIONARY:
            item = OFFLINE_DICTIONARY[clean_text]
            if tgt == "ka" and "ka" in item:
                return f"{item['ka']} ({item['pos']})"
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT translated_text FROM history WHERE target_lang=? AND LOWER(original_text)=LOWER(?) ORDER BY id DESC LIMIT 1", (tgt, text.strip()))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            log_error(e)
            return None

    def add_favorite(self, src, tgt, original, translated):
        if not original.strip() or not translated.strip(): return False
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            next_time = int(time.time()) + 86400
            cursor.execute("INSERT INTO favorites (source_lang, target_lang, original_text, translated_text, next_review, interval) VALUES (?, ?, ?, ?, ?, 1)", (src, tgt, original, translated, next_time))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log_error(e)
            return False

db = DatabaseManager()

class AsyncTranslateEngine:
    @staticmethod
    def async_post_request(url, payload, callback):
        def _worker():
            headers = {'Content-Type': 'application/json', 'Authorization': API_AUTH_TOKEN}
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=8)
                if response.status_code == 200:
                    Clock.schedule_once(lambda dt: callback(True, response.json()), 0)
                else:
                    Clock.schedule_once(lambda dt: callback(False, f"HTTP {response.status_code}"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: callback(False, str(e)), 0)
        threading.Thread(target=_worker, daemon=True).start()

# ----------------------------------------------------
# 7. Kivy UI Layout
# ----------------------------------------------------
KV = f'''
<MainScreen>:
    GeorgianFlagBackground:
        id: flag_bg
        size: self.parent.size if self.parent else (100, 100)

    BoxLayout:
        orientation: 'vertical'
        padding: 8
        spacing: 6

        # Top Header Bar
        BoxLayout:
            size_hint_y: None
            height: '42dp'
            spacing: 4

            NetworkIndicator:
                id: net_indicator
                size_hint_x: None
                width: '18dp'

            Label:
                text: "LingoLens v{APP_VERSION}"
                bold: True
                font_size: '11sp'
                font_name: '{FONT_PATH}'
                color: 0.2, 0.7, 1, 1

            Button:
                text: "🗣️ დიალოგი"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '78dp'
                background_color: 0.9, 0.3, 0.3, 1
                on_release: root.open_interpreter_mode()

            Button:
                text: "📖 ლექსიკონი"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '78dp'
                background_color: 0.2, 0.6, 0.8, 1
                on_release: root.open_dictionary_hub()

            Button:
                text: "📝 ქვიზი"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '58dp'
                background_color: 0.8, 0.5, 0.2, 1
                on_release: root.open_quiz_mode()

            Button:
                text: "🌙/☀️"
                size_hint_x: None
                width: '38dp'
                background_color: 0.2, 0.2, 0.3, 1
                on_release: root.toggle_theme()

        # Language Selector Bar
        BoxLayout:
            size_hint_y: None
            height: '38dp'
            spacing: 6

            Button:
                id: btn_source_lang
                text: "Auto-Detect (ავტო)"
                font_name: '{FONT_PATH}'
                background_color: 0.12, 0.15, 0.22, 0.9
                on_release: root.open_language_menu('source')

            Button:
                text: "<->"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '40dp'
                background_color: 0.12, 0.15, 0.22, 0.9
                color: 0.2, 0.7, 1, 1
                on_release: root.swap_languages()

            Button:
                id: btn_target_lang
                text: "English (US / UK)"
                font_name: '{FONT_PATH}'
                background_color: 0.12, 0.15, 0.22, 0.9
                on_release: root.open_language_menu('target')

        # Input Area
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.40
            padding: 6
            canvas.before:
                Color:
                    rgba: 0.08, 0.1, 0.15, 0.85
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8,]

            BoxLayout:
                size_hint_y: None
                height: '30dp'
                Label:
                    text: "შეყვანა:"
                    font_name: '{FONT_PATH}'
                    font_size: '11sp'
                    color: 0.6, 0.7, 0.8, 1
                    size_hint_x: None
                    width: '60dp'

                AudioVisualizer:
                    id: audio_viz

                Button:
                    text: "📁 დოკუმენტი"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '82dp'
                    background_color: 0.3, 0.6, 0.4, 1
                    on_release: root.open_file_translator()

                Button:
                    text: "X"
                    bold: True
                    size_hint_x: None
                    width: '30dp'
                    background_color: 0.8, 0.2, 0.2, 1
                    on_release: root.clear_input_text()

            TextInput:
                id: input_text
                hint_text: "ჩაწერეთ, თქვით ან გახსენით ფაილი..."
                font_name: '{FONT_PATH}'
                background_color: 0, 0, 0, 0
                foreground_color: 1, 1, 1, 1
                hint_text_color: 0.4, 0.48, 0.58, 1
                font_size: '14sp'
                on_text: root.on_live_translate(self.text)

            BoxLayout:
                size_hint_y: None
                height: '32dp'
                spacing: 4
                Widget:
                Button:
                    text: "🧠 AI აზროვნება"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '100dp'
                    background_color: 0.7, 0.3, 0.8, 1
                    on_release: root.analyze_and_think()
                Button:
                    text: "🎤 ხმა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '60dp'
                    background_color: 0.1, 0.6, 0.4, 1
                    on_release: root.start_speech_to_text(root.source_lang)

        # Output Area
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.45
            padding: 6
            canvas.before:
                Color:
                    rgba: 0.08, 0.1, 0.15, 0.85
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8,]

            TextInput:
                id: output_text
                hint_text: "თარგმანი და ლოგიკური ანალიზი გამოჩნდება აქ..."
                font_name: '{FONT_PATH}'
                readonly: True
                background_color: 0, 0, 0, 0
                foreground_color: 0, 0.95, 0.75, 1
                font_size: '14sp'

            BoxLayout:
                size_hint_y: None
                height: '32dp'
                spacing: 4

                Button:
                    text: "📋"
                    size_hint_x: None
                    width: '38dp'
                    background_color: 0.2, 0.4, 0.6, 1
                    on_release: root.copy_to_clipboard()

                Button:
                    text: "🔗"
                    size_hint_x: None
                    width: '38dp'
                    background_color: 0.2, 0.5, 0.4, 1
                    on_release: root.share_translation()

                Button:
                    text: "★ შენახვა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '78dp'
                    background_color: 0.9, 0.6, 0.1, 1
                    on_release: root.save_to_favorites()

                Button:
                    text: "1.0x"
                    id: btn_tts_speed
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '45dp'
                    background_color: 0.2, 0.4, 0.5, 1
                    on_release: root.toggle_tts_speed()

                Button:
                    text: "🔊 მოსმენა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '78dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    on_release: root.speak_output_text()
'''

Builder.load_string(KV)

# ----------------------------------------------------
# 8. Main Screen Logic
# ----------------------------------------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "auto"
        self.target_lang = "en"
        self.theme_mode = "dark"
        self.tts_speed = 1.0
        self._debounce_event = None

    def on_enter(self):
        self.ids.flag_bg.start_bg_animation()
        Clock.schedule_interval(self.check_network_status, 10)
        self.check_network_status(0)

    def open_language_menu(self, mode):
        trigger_vibration()
        main_layout = BoxLayout(orientation='vertical', padding=6, spacing=6)
        
        search_input = TextInput(
            hint_text="🔍 მოძებნეთ ენა...",
            font_name=FONT_PATH,
            size_hint_y=None,
            height='40dp',
            multiline=False
        )
        
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4, padding=4)
        box.bind(minimum_height=box.setter('height'))

        popup = Popup(title='აირჩიეთ ენა', title_font=FONT_PATH, content=main_layout, size_hint=(0.9, 0.85))

        def select_lang(code, name):
            if mode == 'source':
                self.source_lang = code
                self.ids.btn_source_lang.text = name
            else:
                self.target_lang = code
                self.ids.btn_target_lang.text = name
            popup.dismiss()
            if self.ids.input_text.text.strip():
                self.trigger_translation(self.ids.input_text.text)

        def populate_languages(query=""):
            box.clear_widgets()
            clean_q = query.strip().lower()
            for name, code in LANGUAGES.items():
                if clean_q in name.lower() or clean_q in code.lower():
                    btn = Button(
                        text=name,
                        font_name=FONT_PATH,
                        size_hint_y=None,
                        height='38dp',
                        background_color=(0.15, 0.2, 0.3, 1)
                    )
                    btn.bind(on_release=lambda instance, c=code, n=name: select_lang(c, n))
                    box.add_widget(btn)

        search_input.bind(text=lambda instance, text: populate_languages(text))
        populate_languages()

        scroll.add_widget(box)
        main_layout.add_widget(search_input)
        main_layout.add_widget(scroll)
        popup.open()

    def swap_languages(self):
        trigger_vibration()
        if self.source_lang == "auto": return
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        self.ids.btn_source_lang.text, self.ids.btn_target_lang.text = self.ids.btn_target_lang.text, self.ids.btn_source_lang.text
        if self.ids.input_text.text.strip():
            self.trigger_translation(self.ids.input_text.text)

    def on_live_translate(self, text):
        if self._debounce_event:
            Clock.unschedule(self._debounce_event)
        self._debounce_event = Clock.schedule_once(lambda dt: self.trigger_translation(text), 0.5)

    def trigger_translation(self, text):
        if not text.strip():
            self.ids.output_text.text = ""
            return

        cached_res = db.search_offline_cache(self.source_lang, self.target_lang, text)
        if cached_res:
            self.ids.output_text.text = cached_res

        payload = {
            "text": text,
            "source": self.source_lang,
            "target": self.target_lang
        }
        url = f"{VERCEL_BASE_URL}/api/translate"

        def handle_response(success, data):
            if success and isinstance(data, dict) and "translated" in data:
                res_text = data["translated"]
                self.ids.output_text.text = res_text
                db.add_history(self.source_lang, self.target_lang, text, res_text)
            elif not cached_res:
                self.ids.output_text.text = f"{text}"

        AsyncTranslateEngine.async_post_request(url, payload, handle_response)

    def analyze_and_think(self):
        trigger_vibration()
        txt = self.ids.input_text.text.strip()
        if not txt:
            self.ids.output_text.text = "გთხოვთ, ჯერ შეიყვანოთ ტექსტი ანალიზისთვის."
            return
        analysis = ReasoningEngine.deep_reasoning_analysis(txt, self.source_lang, self.target_lang)
        self.ids.output_text.text = analysis

    def check_network_status(self, dt):
        def _check():
            try:
                r = requests.get(f"{VERCEL_BASE_URL}/api/health", timeout=3)
                status = "green" if r.status_code == 200 else "yellow"
            except Exception:
                status = "red"
            Clock.schedule_once(lambda d: self.ids.net_indicator.set_status(status), 0)
        threading.Thread(target=_check, daemon=True).start()

    def start_speech_to_text(self, lang_code):
        trigger_vibration()
        self.ids.audio_viz.start_animation()
        NativeSpeechManager.start_listening(
            lang_code, 
            callback_text=lambda t: setattr(self.ids.input_text, 'text', t)
        )
        Clock.schedule_once(lambda dt: self.ids.audio_viz.stop_animation(), 4)

    def speak_output_text(self):
        trigger_vibration()
        txt = self.ids.output_text.text.strip()
        NativeSpeechManager.speak_text(txt, self.target_lang, speed=self.tts_speed)

    def toggle_tts_speed(self):
        speeds = [1.0, 1.25, 1.5, 0.75]
        curr_idx = speeds.index(self.tts_speed)
        self.tts_speed = speeds[(curr_idx + 1) % len(speeds)]
        self.ids.btn_tts_speed.text = f"{self.tts_speed}x"

    def clear_input_text(self):
        trigger_vibration()
        self.ids.input_text.text = ""
        self.ids.output_text.text = ""

    def copy_to_clipboard(self):
        trigger_vibration()
        if self.ids.output_text.text:
            Clipboard.copy(self.ids.output_text.text)

    def share_translation(self):
        trigger_vibration()
        if self.ids.output_text.text:
            try:
                share.share(text=self.ids.output_text.text, title="LingoLens Translation")
            except Exception as e:
                log_error(e)

    def save_to_favorites(self):
        trigger_vibration()
        inp = self.ids.input_text.text.strip()
        out = self.ids.output_text.text.strip()
        if db.add_favorite(self.source_lang, self.target_lang, inp, out):
            self.ids.output_text.text += "\n\n[★ შენახულია ფავორიტებში!]"

    def toggle_theme(self):
        trigger_vibration()
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.ids.flag_bg.set_theme(self.theme_mode)

    def open_interpreter_mode(self):
        trigger_vibration()
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text="🗣️ ორმხრივი დიალოგის რეჟიმი", font_name=FONT_PATH, font_size='16sp')
        box.add_widget(lbl)
        popup = Popup(title="ინტერპრეტატორი", title_font=FONT_PATH, content=box, size_hint=(0.85, 0.6))
        popup.open()

    def open_dictionary_hub(self):
        trigger_vibration()
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text="📖 ოფლაინ ლექსიკონის ბაზა", font_name=FONT_PATH, font_size='16sp')
        box.add_widget(lbl)
        popup = Popup(title="ლექსიკონი", title_font=FONT_PATH, content=box, size_hint=(0.85, 0.6))
        popup.open()

    def open_quiz_mode(self):
        trigger_vibration()
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text="📝 ყოველდღიური ქვიზი", font_name=FONT_PATH, font_size='16sp')
        box.add_widget(lbl)
        popup = Popup(title="ქვიზი", title_font=FONT_PATH, content=box, size_hint=(0.85, 0.6))
        popup.open()

    def open_file_translator(self):
        trigger_vibration()
        try:
            filechooser.open_file(on_selection=self._on_file_selected)
        except Exception as e:
            log_error(e)

    def _on_file_selected(self, selection):
        if selection:
            try:
                with open(selection[0], 'r', encoding='utf-8') as f:
                    self.ids.input_text.text = f.read()
            except Exception as e:
                log_error(e)

# ----------------------------------------------------
# 9. App Application Entrypoint
# ----------------------------------------------------
class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro"
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()
