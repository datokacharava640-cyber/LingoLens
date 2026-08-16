import os
import json
import sqlite3
import threading
from datetime import datetime

import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner

# ---------------------------------------------------------
# Local Modules Import (Fail-Safe & Environment Config)
# ---------------------------------------------------------
try:
    from modules.config import Config
except ImportError:
    class Config:
        GEMINI_API_KEY = ""

# Pure Python PDF Parser
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    from plyer import tts, filechooser
except Exception:
    tts, filechooser = None, None


# ---------------------------------------------------------
# 1. ADVANCED DATABASE & FLASHCARDS MANAGER (SQLite)
# ---------------------------------------------------------
class DatabaseManager:
    def __init__(self, db_name="lingolens.db"):
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                db_dir = app_storage_path()
            else:
                db_dir = "."
            self.db_path = os.path.join(db_dir, db_name)
            self.create_tables()
            self.seed_offline_dictionary()
        except Exception as e:
            print(f"DB Init Error: {e}")

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_text TEXT,
                        translated_text TEXT,
                        timestamp DATETIME
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dictionary (
                        word TEXT PRIMARY KEY,
                        translation TEXT
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS flashcards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        word TEXT UNIQUE,
                        translation TEXT,
                        review_count INTEGER DEFAULT 0,
                        next_review DATETIME
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"Create Tables Error: {e}")

    def seed_offline_dictionary(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM dictionary")
                if cursor.fetchone()[0] == 0:
                    basic_words = [
                        ("hello", "გამარჯობა"), ("world", "სამყარო"), ("friend", "მეგობარი"),
                        ("thank you", "გმადლობთ"), ("good", "კარგი"), ("bad", "ცუდი"),
                        ("yes", "დიახ"), ("no", "არა"), ("please", "გეთაყვა"),
                        ("book", "წიგნი"), ("water", "წყალი"), ("love", "სიყვარული"),
                        ("computer", "კომპიუტერი"), ("language", "ენა"), ("camera", "კამერა")
                    ]
                    cursor.executemany("INSERT OR IGNORE INTO dictionary VALUES (?, ?)", basic_words)
                    conn.commit()
        except Exception as e:
            print(f"Seed DB Error: {e}")

    def add_history(self, src, trans):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO history (source_text, translated_text, timestamp) VALUES (?, ?, ?)",
                               (src, trans, datetime.now()))
                conn.commit()
        except Exception as e:
            print(f"DB Add Error: {e}")

    def get_history(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT source_text, translated_text FROM history ORDER BY id DESC LIMIT 15")
                return cursor.fetchall()
        except Exception as e:
            print(f"DB Read Error: {e}")
            return []

    def save_flashcard(self, word, translation):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO flashcards (word, translation, next_review)
                    VALUES (?, ?, ?)
                """, (word, translation, datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            print(f"Flashcard Save Error: {e}")
            return False

    def translate_offline(self, text):
        try:
            words = text.lower().strip().split()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                result = []
                for w in words:
                    cursor.execute("SELECT translation FROM dictionary WHERE word=?", (w,))
                    row = cursor.fetchone()
                    result.append(row[0] if row else f"[{w}]")
                return " ".join(result)
        except Exception as e:
            print(f"Offline Translation Error: {e}")
            return text


# ---------------------------------------------------------
# 2. REAL-TIME SERVICE MANAGER (Live AI, TTS, OCR, Stream)
# ---------------------------------------------------------
class ServiceManager:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('APP_GEMINI_API_KEY') or getattr(Config, 'GEMINI_API_KEY', '')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.is_listening = False

    def check_network(self):
        try:
            requests.get("https://1.1.1.1", timeout=1.2)
            return True
        except Exception:
            return False

    def query_gemini_realtime(self, text, mode="General", tone="Standard"):
        if not self.check_network():
            return None, "Offline"

        prompt = (
            f"Context Mode: {mode}, Tone: {tone}.\n"
            f"Translate the following text accurately between Georgian and English.\n"
            f"Return ONLY a JSON object with keys 'translation' and 'grammar'.\n"
            f"Text: {text}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        endpoint = f"{self.api_url}?key={self.api_key}"

        try:
            res = requests.post(endpoint, json=payload, timeout=6)
            if res.status_code == 200:
                data = res.json()
                raw_response = data['candidates'][0]['content']['parts'][0]['text']
                cleaned = raw_response.replace("```json", "").replace("
