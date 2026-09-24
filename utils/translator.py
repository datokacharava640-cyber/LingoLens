# ==============================================================================
# LingoLens AI - Translator Module
# Copyright (c) 2026 Dato Kacharava. All rights reserved.
#
# This software is licensed under the MIT License.
# See the LICENSE file in the root directory for full license information.
# ==============================================================================

import threading
import requests
import json
import base64
import time
import hmac
import hashlib
import config

# LingoLens ცენტრალური სერვერის მისამართი
SERVER_URL = "https://api.lingolens.app/api/v1/translate"

# საიდუმლო გასაღები მოთხოვნის ავთენტურობის დასადასტურებლად
# (ეს გასაღები იდენტური უნდა იყოს სერვერის .env ფაილში)
APP_SECRET_KEY = getattr(config, 'APP_SECRET_KEY', 'LingoLens_Super_Secret_Key_2026')


def generate_signature(timestamp: str) -> str:
    """ქმნის უნიკალურ HMAC-SHA256 ხელმოწერას დროის შტამპის მიხედვით."""
    message = f"{timestamp}:{APP_SECRET_KEY}"
    return hmac.new(
        APP_SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def translate_via_lingolens_server(text, src_lang, target_lang):
    """საკუთარ ცენტრალურ სერვერთან დაკავშირების უსაფრთხო ფუნქცია"""
    timestamp = str(int(time.time()))
    signature = generate_signature(timestamp)

    # უსაფრთხოების ჰედერები
    headers = {
        "Content-Type": "application/json",
        "X-App-Timestamp": timestamp,
        "X-App-Signature": signature
    }

    payload = {
        "text": text,
        "src_lang": src_lang,
        "target_lang": target_lang
    }

    try:
        response = requests.post(SERVER_URL, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get("result")
        else:
            print(f"LingoLens სერვერის პასუხი: {response.status_code}")
    except Exception as e:
        print("LingoLens სერვერის კავშირის შეცდომა:", e)
    return None


def translate_text(prompt, text, src_lang, target_lang, callback):
    """ტექსტის თარგმნის მთავარი ფუნქცია (ასინქრონული)"""
    def _worker():
        try:
            # 1. ჯერ ვცდილობთ პასუხის მიღებას შენი საკუთარი სერვერიდან
            server_res = translate_via_lingolens_server(text, src_lang, target_lang)
            if server_res:
                callback(server_res)
                return

            # 2. თუ შენი სერვერი მიუწვდომელია, გადადის Gemini API-ზე (Fallback)
            api_key = getattr(config, 'GEMINI_API_KEY', '')
            if not api_key:
                callback("გთხოვთ მიუთითოთ API Key პარამეტრებში")
                return

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}

            res = requests.post(url, json=payload, headers=headers, timeout=12)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        callback(parts[0].get('text', ''))
                        return
                callback("თარგმანი ვერ მოიძებნა")
            else:
                callback(f"API შეცდომა: {res.status_code}")
        except Exception as e:
            callback(f"შეცდომა: {str(e)}")

    threading.Thread(target=_worker, daemon=True).start()


def analyze_image_and_translate(image_path, target_lang, callback):
    """სურათიდან ტექსტის ამოცნობისა და თარგმნის (OCR) ფუნქცია"""
    def _worker():
        try:
            api_key = getattr(config, 'GEMINI_API_KEY', '')
            if not api_key:
                callback("გთხოვთ მიუთითოთ API Key პარამეტრებში")
                return

            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            
            prompt_text = f"Extract all text from this image accurately and translate it into {target_lang}."
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": encoded_string
                            }
                        }
                    ]
                }]
            }

            res = requests.post(url, json=payload, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        callback(parts[0].get('text', ''))
                        return
                callback("ტექსტი ვერ ამოიცნო")
            else:
                callback(f"OCR შეცდომა: {res.status_code}")
        except Exception as e:
            callback(f"შეცდომა: {str(e)}")

    threading.Thread(target=_worker, daemon=True).start()
