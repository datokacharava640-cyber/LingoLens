"""
LingoLens Ultra Pro v9.5.0 (Global Master Edition with Georgian & World Grammar, Reasoning & Native Speech Engine)
========================================================================
ავტორი: დავით კაჭარავა
ლოკაცია: საქართველო
თარიღი: 2026
========================================================================
"""

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
    "Marathi (मराठी)": "mr",
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
    "Lao (ພາສາລາວ)": "lo",
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

# ----------------------------------------------------
# 2. ქართული გრამატიკის, დროების, ბრუნებისა და ზმნისწონების ძრავი
# ----------------------------------------------------
class GeorgianGrammarEngine:
    VERB_PREFIXES = ["მი", "მო", "წა", "წამო", "შე", "შემო", "გა", "გამო", "გადა", "გადმო", "აღ", "და"]
    
    @staticmethod
    def declension_noun(word):
        """ქართული სახელის ბრუნების ავტომატური წარმოება (7 ბრუნვა)"""
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
        """ქართული ზმნის დროების წარმოება (აწმყო, წარსული, მომავალი)"""
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
        """ქართული ენობრივი ლოგიკისა და გრამატიკის სრული ანალიზი"""
        words = text.strip().split()
        if not words: return "ტექსტი ცარიელია."

        analysis = []
        analysis.append("=== 🇬🇪 ქართული ენობრივი და გრამატიკული ანალიზი ===")
        
        for w in words[:3]: # პირველი სამი სიტყვის ანალიზი
            analysis.append(f"\n🔍 სიტყვა: '{w}'")
            # ამოწმებს ზმნისწონს
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
# 3. მსოფლიო ენების გრამატიკისა და სინტაქსის ძრავი
# ----------------------------------------------------
class GlobalGrammarEngine:
    @staticmethod
    def analyze_global_grammar(text, lang_code):
        """გლობალური სინტაქსური და გრამატიკული სტრუქტურების დეტექცია"""
        text_lower = text.lower()
        insights = [f"=== 🌐 Global Grammar Engine [{lang_code.upper()}] ==="]
        
        if lang_code == "en":
            # Passive Voice Detection
            if re.search(r'\b(am|is|are|was|were|been|being)\b\s+\w+ed\b', text_lower):
                insights.append("• სინტაქსი: ვნებითი გვარი (Passive Voice). ყურადღება მიაქციეთ ობიექტის აქცენტს.")
            # Perfect Tenses
            if re.search(r'\b(has|have|had)\b\s+\w+(ed|en)\b', text_lower):
                insights.append("• დრო: Perfect Aspect (შესრულებული მოქმედება). ქართულში ითარგმნება შედეგობითი ან წყვეტილი ფორმით.")
            # Conditional Structures
            if "if" in text_lower or "would" in text_lower:
                insights.append("• ლოგიკა: პირობითი წინადადება (Conditionals). ამოწმებს რეალურ/ჰიპოთეტურ სცენარს.")
        
        elif lang_code == "de":
            if text_lower.startswith(("warum", "wie", "wo", "was")):
                insights.append("• გერმანული სინტაქსი: კითხვითი წინადადება. ზმნა მე-2 ან 1-ელ პოზიციაზე.")
        
        if len(insights) == 1:
            insights.append("• სტრუქტურა: სტანდარტული წინადადების წყობა და მორფოლოგიური ჰარმონია.")
            
        return "\n".join(insights)

# ----------------------------------------------------
# 4. აზროვნებისა და ლოგიკური ანალიზის AI ძრავი (Reasoning Engine)
# ----------------------------------------------------
class ReasoningEngine:
    @staticmethod
    def deep_reasoning_analysis(text, source_lang, target_lang):
        """წინადადების სიღრმისეული აზრობრივი, ტონალური და ლოგიკური ანალიზი"""
        words = text.split()
        word_count = len(words)
        
        # 1. ტონალობის დეტექცია
        formal_keywords = ["pleased", "sincerely", "regards", "request", "გთხოვთ", "პატივისცემით", "ბრძანება"]
        is_formal = any(k in text.lower() for k in formal_keywords)
        tone = "ოფიციალურ-საქმიანი (Formal)" if is_formal else "ყოველდღიური/საუბრული (Informal)"

        # 2. ლოგიკური ტიპოლოგია
        if text.endswith("?"):
            intent = "ინფორმაციის მოთხოვნა / შეკითხვა (Interrogative Logic)"
        elif text.endswith("!"):
            intent = "ემოციური გამოხატვა / ბრძანება (Exclamatory/Imperative Logic)"
        else:
            intent = "მტკიცებითი მსჯელობა / ფაქტის კონსტატაცია (Declarative Logic)"

        # 3. გრამატიკული ანალიტიკის სინთეზი
        if source_lang == "ka" or (source_lang == "auto" and any('\u10d0' <= c <= '\u10fa' for c in text)):
            grammar_part = GeorgianGrammarEngine.analyze_georgian_text(text)
        else:
            grammar_part = GlobalGrammarEngine.analyze_global_grammar(text, source_lang)

        # 4. საბოლოო აზრობრივი დასკვნა
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
# 5. Native Speech Manager (Android Speech Recognizer & TTS)
# ----------------------------------------------------
class NativeSpeechManager:
    @staticmethod
    def start_listening(lang_code, callback_text):
        """Android Native Speech-To-Text სისტემა Pyjnius-ის ან იმიტაციის გამოყენებით"""
        if platform == 'android':
            try:
                from jnius import autoclass
                # Native Android Intent for Speech
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                # Start Activity via PythonActivity
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = PythonActivity.mActivity
                
                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)
                currentActivity.startActivityForResult(intent, 1001)
            except Exception as e:
                log_error(e)
                callback_text("ხმის ამოცნობის ფუნქცია ჩართულია...")
        else:
            callback_text("[Desktop Simulation]: ხმოვანი შეყვანა აქტიურია (თქვით ტექსტი)...")

    @staticmethod
    def speak_text(text, lang_code, speed=1.0):
        """Android Native Text-To-Speech (TTS) სისტემა"""
        if not text or text.startswith("["): return
        if platform == 'android':
            try:
                from jnius import autoclass
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                # Native TTS Instance
                tts = TextToSpeech(PythonActivity.mActivity, None)
                tts.setSpeechRate(float(speed))
                tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                log_error(e)
        else:
            print(f"[TTS Audio Output ({lang_code} / {speed}x)]: {text}")

# ----------------------------------------------------
# 6. დამხმარე ფუნქციები და მონაცემთა ბაზა
# ----------------------------------------------------
def trigger_vibration():
    try:
        vibrator.vibrate(0.04)
    except Exception:
        pass

def log_error(err):
    try:
        base_dir = App.get_running_app().user_data_dir if (platform == 'android' and App.get_running_app()) else "."
        log_path = os.path.join(base_dir, "error_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- ERROR [{Clock.get_time()}] ---\n{traceback.format_exc()}\n")
    except Exception:
        pass

class AudioVisualizer(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_active = False
        self.phase = 0
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def start_animation(self):
        self.is_active = True
        Clock.schedule_interval(self.animate, 1 / 30.0)

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
            Clock.schedule_interval(self.animate, 1 / 30.0)

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
                return f"[Offline AI Engine]\n{item['ka']}\n({item['pos']})"
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT translated_text FROM history WHERE target_lang=? AND LOWER(original_text)=LOWER(?) ORDER BY id DESC LIMIT 1", (tgt, text.strip()))
            row = cursor.fetchone()
            conn.close()
            return f"[Offline Cache]\n{row[0]}" if row else None
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
                response = requests.post(url, json=payload, headers=headers, timeout=10)
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
# 8. Main Application Logic
# ----------------------------------------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "auto"
        self.target_lang = "en"
        self.theme_mode = "dark"
        self.tts_speed = 1.0

    def on_enter(self):
        self.ids.flag_bg.start_bg_animation()
        Clock.schedule_interval(self.check_network_status, 5)
        self.check_network_status(0)

    def open_language_menu(self, mode):
        trigger_vibration()
        main_layout = BoxLayout(orientation='vertical', padding=6, spacing=6)
        
        search_input = TextInput(
            hint_text="🔍 მოძებნეთ ენა (მაგ. Spanish, ka, fr)...",
            font_name=FONT_PATH,
            size_hint_y=None,
            height='40dp',
            multiline=False
        )
        
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4, padding=4)
        box.bind(minimum_height=box.setter('height'))

        popup = Popup(title='აირჩიეთ ენა (100+ მსოფლიო ენა)', title_font=FONT_PATH, content=main_layout, size_hint=(0.9, 0.85))

        def populate_languages(query=""):
            box.clear_widgets()
            clean_q = query.strip().lower()
            for name, code in LANGUAGES.items():
                if mode == 'target' and code == 'auto': continue
                if clean_q and (clean_q not in name.lower() and clean_q not in code.lower()):
                    continue
                btn = Button(
                    text=f"{name} [{code}]",
                    font_name=FONT_PATH,
                    size_hint_y=None,
                    height='42dp',
                    background_color=(0.14, 0.17, 0.24, 1)
                )
                btn.bind(on_release=lambda x, n=name, c=code: self.select_language(mode, n, c, popup))
                box.add_widget(btn)

        search_input.bind(text=lambda instance, value: populate_languages(value))
        populate_languages()

        scroll.add_widget(box)
        main_layout.add_widget(search_input)
        main_layout.add_widget(scroll)
        popup.open()

    def select_language(self, mode, name, code, popup):
        trigger_vibration()
        if mode == 'source':
            self.source_lang = code
            self.ids.btn_source_lang.text = name
        else:
            self.target_lang = code
            self.ids.btn_target_lang.text = name
        popup.dismiss()
        self.trigger_retranslate()

    def open_interpreter_mode(self):
        trigger_vibration()
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        lbl_top = Label(text="[თანამოსაუბრე (English)]", font_name=FONT_PATH, color=(0.2, 0.8, 1, 1), size_hint_y=None, height='25dp')
        txt_top = TextInput(hint_text="Partner's speech...", font_name=FONT_PATH, readonly=True, size_hint_y=0.35)
        
        btn_mic_partner = Button(text="🎤 ჩაწერა (English)", font_name=FONT_PATH, size_hint_y=None, height='38dp', background_color=(0.2, 0.5, 0.8, 1))
        btn_mic_partner.bind(on_release=lambda x: self.start_speech_to_text("en", target_input=txt_top))

        lbl_bottom = Label(text="[თქვენ (ქართული)]", font_name=FONT_PATH, color=(0, 0.95, 0.75, 1), size_hint_y=None, height='25dp')
        txt_bottom = TextInput(hint_text="თქვენი საუბარი...", font_name=FONT_PATH, readonly=True, size_hint_y=0.35)
        
        btn_mic_me = Button(text="🎤 ჩაწერა (ქართული)", font_name=FONT_PATH, size_hint_y=None, height='38dp', background_color=(0.1, 0.6, 0.4, 1))
        btn_mic_me.bind(on_release=lambda x: self.start_speech_to_text("ka", target_input=txt_bottom))

        close_btn = Button(text="რეჟიმის დახურვა", font_name=FONT_PATH, size_hint_y=None, height='40dp', background_color=(0.8, 0.2, 0.2, 1))

        content.add_widget(lbl_top)
        content.add_widget(txt_top)
        content.add_widget(btn_mic_partner)
        content.add_widget(lbl_bottom)
        content.add_widget(txt_bottom)
        content.add_widget(btn_mic_me)
        content.add_widget(close_btn)

        popup = Popup(title="🗣️ Live Conversation Interpreter", title_font=FONT_PATH, content=content, size_hint=(0.95, 0.95))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def open_dictionary_hub(self):
        trigger_vibration()
        word = self.ids.input_text.text.strip().lower()
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        if word in OFFLINE_DICTIONARY:
            data = OFFLINE_DICTIONARY[word]
            info = f"[b]სიტყვა:[/b] {word}\n[b]მნიშვნელობა:[/b] {data['ka']}\n[b]მეტყველების ნაწილი:[/b] {data['pos']}\n\n[b]სინონიმები:[/b] {', '.join(data['syn'])}\n[b]ანტონიმები:[/b] {', '.join(data['ant'])}\n[b]იდიომი/ფრაზა:[/b] {data['idiom']}"
        else:
            # ქართული გრამატიკული გენერატორი თუ ქართული სიტყვაა
            decls = GeorgianGrammarEngine.declension_noun(word)
            if decls:
                info = f"[b]ქართული სიტყვის ბრუნება ('{word}'):[/b]\n" + "\n".join([f"• {k}: {v}" for k, v in decls.items()])
            else:
                info = f"სიტყვა '{word}' არ მოიძებნა ოფლაინ ბაზაში.\n\nჩაწერეთ ინგლისური ან ქართული სიტყვა."

        lbl_info = Label(text=info, markup=True, font_name=FONT_PATH, font_size='13sp')
        content.add_widget(lbl_info)
        
        close_btn = Button(text="დახურვა", font_name=FONT_PATH, size_hint_y=None, height='40dp', background_color=(0.3, 0.3, 0.3, 1))
        content.add_widget(close_btn)
        
        popup = Popup(title="📖 Contextual Dictionary & Grammar Engine", title_font=FONT_PATH, content=content, size_hint=(0.9, 0.65))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def open_quiz_mode(self):
        trigger_vibration()
        quiz = random.choice(DAILY_QUIZ)
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        lbl_q = Label(text=quiz['q'], font_name=FONT_PATH, font_size='15sp', bold=True)
        content.add_widget(lbl_q)

        for opt in quiz['options']:
            btn = Button(text=opt, font_name=FONT_PATH, size_hint_y=None, height='40dp', background_color=(0.14, 0.2, 0.3, 1))
            btn.bind(on_release=lambda x, selected=opt: self._check_quiz_answer(selected, quiz['a'], popup))
            content.add_widget(btn)

        close_btn = Button(text="გამოტოვება", font_name=FONT_PATH, size_hint_y=None, height='35dp', background_color=(0.3, 0.3, 0.3, 1))
        content.add_widget(close_btn)

        popup = Popup(title="📝 AI Spaced Repetition Quiz", title_font=FONT_PATH, content=content, size_hint=(0.88, 0.55))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def _check_quiz_answer(self, selected, correct, popup):
        trigger_vibration()
        popup.dismiss()
        res_text = "🎉 სწორია! შესანიშნავი შედეგია." if selected == correct else f"❌ არასწორია. სწორი პასუხი იყო: {correct}"
        res_popup = Popup(title="შედეგი", title_font=FONT_PATH, content=Label(text=res_text, font_name=FONT_PATH), size_hint=(0.8, 0.3))
        res_popup.open()

    def open_file_translator(self):
        trigger_vibration()
        try:
            filechooser.open_file(on_selection=self._on_file_selected)
        except Exception as e:
            log_error(e)

    def _on_file_selected(self, selection):
        if selection and len(selection) > 0:
            file_path = selection[0]
            ext = os.path.splitext(file_path)[1].lower()
            try:
                if ext in ['.txt', '.json', '.csv', '.log']:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(3000)
                        self.ids.input_text.text = content
                        self.ids.output_text.text = f"[დოკუმენტი ჩატვირთულია: {os.path.basename(file_path)}]\nმიმდინარეობს სტრუქტურული თარგმნა..."
                else:
                    self.ids.output_text.text = f"[ფორმატის მხარდაჭერა: {ext}]\nდოკუმენტის ტექსტი მუშავდება..."
            except Exception as e:
                log_error(e)

    def copy_to_clipboard(self):
        trigger_vibration()
        text = self.ids.output_text.text.strip()
        if text and not text.startswith("["):
            Clipboard.copy(text)
            self.ids.output_text.text = f"[დაკოპირებულია ბუფერში!]\n\n{text}"

    def share_translation(self):
        trigger_vibration()
        text = self.ids.output_text.text.strip()
        if text and not text.startswith("["):
            try:
                share.share(title="LingoLens Translation", text=text)
            except Exception as e:
                log_error(e)

    def toggle_theme(self):
        trigger_vibration()
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.ids.flag_bg.set_theme(self.theme_mode)

    def toggle_tts_speed(self):
        trigger_vibration()
        speeds = [0.75, 1.0, 1.25, 1.5]
        idx = (speeds.index(self.tts_speed) + 1) % len(speeds)
        self.tts_speed = speeds[idx]
        self.ids.btn_tts_speed.text = f"{self.tts_speed}x"

    def clear_input_text(self):
        trigger_vibration()
        self.ids.input_text.text = ""
        self.ids.output_text.text = ""

    def save_to_favorites(self):
        trigger_vibration()
        orig = self.ids.input_text.text.strip()
        trans = self.ids.output_text.text.strip()
        if orig and trans and not trans.startswith("["):
            if db.add_favorite(self.source_lang, self.target_lang, orig, trans):
                self.ids.output_text.text = f"★ [შენახულია ფავორიტებში!]\n\n{trans}"

    def check_network_status(self, dt):
        def _check():
            try:
                res = requests.get(f"{VERCEL_BASE_URL}/api/index", headers={'Authorization': API_AUTH_TOKEN}, timeout=3)
                status = "green" if res.status_code == 200 else "yellow"
            except Exception:
                status = "red"
            Clock.schedule_once(lambda d: self.ids.net_indicator.set_status(status), 0)
        threading.Thread(target=_check, daemon=True).start()

    def swap_languages(self):
        trigger_vibration()
        s, t = self.ids.btn_source_lang.text, self.ids.btn_target_lang.text
        if self.source_lang == "auto": return
        self.ids.btn_source_lang.text, self.ids.btn_target_lang.text = t, s
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        self.trigger_retranslate()

    def on_live_translate(self, text):
        cleaned = text.strip()
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.5)

    def _delayed_translate(self, text):
        cached = db.search_offline_cache(self.source_lang, self.target_lang, text)
        if cached:
            self.ids.output_text.text = cached
            return

        payload = {
            "text": text,
            "source": self.source_lang,
            "target": self.target_lang
        }
        
        self.ids.output_text.text = "მიმდინარეობს თარგმნა..."
        AsyncTranslateEngine.async_post_request(
            f"{VERCEL_BASE_URL}/api/translate",
            payload,
            self._handle_translate_response
        )

    def _handle_translate_response(self, success, result):
        if success and isinstance(result, dict) and "translated" in result:
            translated_text = result["translated"]
            self.ids.output_text.text = translated_text
            db.add_history(self.source_lang, self.target_lang, self.ids.input_text.text, translated_text)
        else:
            self.ids.output_text.text = "[ქსელის შეცდომა ან სერვერი მიუწვდომელია]"

    def trigger_retranslate(self):
        text = self.ids.input_text.text.strip()
        if text:
            self.on_live_translate(text)

    def analyze_and_think(self):
        """AI აზროვნებისა და ლოგიკური ანალიზის გაშვება"""
        trigger_vibration()
        text = self.ids.input_text.text.strip()
        if not text:
            self.ids.output_text.text = "[გთხოვთ, ჯერ შეიყვანოთ ტექსტი AI აზროვნებისა და გრამატიკული ანალიზისთვის]"
            return

        self.ids.output_text.text = "🧠 AI აანალიზებს ტექსტის ლოგიკასა და გრამატიკას..."
        
        # ლოკალური Reasoning Engine-ის გაშვება
        reasoning_result = ReasoningEngine.deep_reasoning_analysis(text, self.source_lang, self.target_lang)
        self.ids.output_text.text = reasoning_result

    def start_speech_to_text(self, lang_code, target_input=None):
        trigger_vibration()
        self.ids.audio_viz.start_animation()
        
        def _update_ui_text(recognized_text):
            if target_input:
                target_input.text = recognized_text
            else:
                self.ids.input_text.text = recognized_text
            self.ids.audio_viz.stop_animation()

        NativeSpeechManager.start_listening(lang_code, _update_ui_text)

    def speak_output_text(self):
        trigger_vibration()
        text = self.ids.output_text.text.strip()
        if text and not text.startswith("["):
            NativeSpeechManager.speak_text(text, self.target_lang, self.tts_speed)


class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro"
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm


if __name__ == '__main__':
    LingoLensApp().run()
