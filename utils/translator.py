import threading
import requests
import urllib3
import json
import os
import config

# Tapē rabipese mo le puipuiga o le SSL i luga o le Android
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SETTINGS_FILE = "settings.json"

def get_api_key():
    # Suʻe muamua le API Key mai le fagu settings.json
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                key = data.get("api_key", "").strip()
                if key:
                    return key
        except Exception as e:
            print("Pulea o fagu Settings Error:", e)
    
    # Afai e leai, faʻaaoga le mea o loʻo i le config.py
    return getattr(config, 'GEMINI_API_KEY', '')

def translate_text(prompt, raw_text, src_lang, target_lang, callback):
    def _worker():
        result = None
        api_key = get_api_key()

        # 1. Gemini REST API Request
        if api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                data = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
                
                response = requests.post(url, json=data, headers=headers, timeout=10, verify=False)
                
                if response.status_code == 200:
                    res_json = response.json()
                    candidates = res_json.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        if parts:
                            result = parts[0].get('text', '').strip()
            except Exception as e:
                print("Gemini Request Error:", e)

        # 2. Google Translate Fallback
        if not result:
            try:
                quoted_text = requests.utils.quote(raw_text)
                fallback_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_lang}&tl={target_lang}&dt=t&q={quoted_text}"
                
                res = requests.get(fallback_url, timeout=5, verify=False).json()
                if res and isinstance(res, list) and len(res) > 0 and res[0]:
                    result = "".join([item[0] for item in res[0] if item and item[0]])
            except Exception as e:
                print("Fallback Error:", e)
                result = "E leʻi mafai ona faʻaliliu (Siaki le Initaneti)"

        if not result:
            result = "Malaia i le faʻaliliuga"

        callback(result)

    threading.Thread(target=_worker, daemon=True).start()
