# ==============================================================================
# LingoLens AI - Central API Backend
# Copyright (c) 2026 Dato Kacharava. All rights reserved.
# ==============================================================================

from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
import redis
import requests
import hmac
import hashlib
import time
import os

app = FastAPI(title="LingoLens Central API")

# 1. Redis ქეშირების ბაზასთან კავშირი
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
except Exception as e:
    print("Redis-თან დაკავშირება ვერ მოხერხდა:", e)
    redis_client = None

# 2. საიდუმლო გასაღები აპლიკაციის ავთენტურობის გადასამოწმებლად
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "LingoLens_Super_Secret_Key_2026")

# 3. Multiple API Key Pool (Gemini Key Rotation)
API_KEYS = [
    os.getenv("GEMINI_KEY_1", ""),
    os.getenv("GEMINI_KEY_2", ""),
    os.getenv("GEMINI_KEY_3", "")
]
# ცარიელი გასაღებების ამოღება
API_KEYS = [k for k in API_KEYS if k]

current_key_index = 0

def get_next_api_key():
    global current_key_index
    if not API_KEYS:
        return None
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return key


def verify_signature(timestamp: str, signature: str) -> bool:
    """გადაამოწმებს აპლიკაციიდან გამოგზავნილ HMAC-SHA256 ხელმოწერას."""
    try:
        req_time = int(timestamp)
        now = int(time.time())
        # Replay Attack-ისგან დაცვა: თუ მოთხოვნა 5 წუთზე (300 წმ) ძველია, უარვყოფთ
        if abs(now - req_time) > 300:
            return False

        message = f"{timestamp}:{APP_SECRET_KEY}"
        expected_signature = hmac.new(
            APP_SECRET_KEY.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        return False


class TranslationRequest(BaseModel):
    text: str
    src_lang: str
    target_lang: str


@app.post("/api/v1/translate")
async def translate(
    req: TranslationRequest,
    x_app_timestamp: str = Header(None, alias="X-App-Timestamp"),
    x_app_signature: str = Header(None, alias="X-App-Signature")
):
    # --- აპლიკაციის უსაფრთხოების შემოწმება ---
    if not x_app_timestamp or not x_app_signature:
        raise HTTPException(status_code=401, detail="Access Denied: Missing Security Headers")

    if not verify_signature(x_app_timestamp, x_app_signature):
        raise HTTPException(status_code=403, detail="Access Denied: Invalid Security Signature")

    # --- ქეშირება (Redis) ---
    cache_key = f"trans:{req.src_lang}:{req.target_lang}:{req.text.strip().lower()}"
    
    if redis_client:
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return {"result": cached_result, "source": "cache"}
        except Exception as e:
            print("Redis-ის წაკითხვის შეცდომა:", e)

    # --- AI მოთხოვნა (Gemini Key Rotation) ---
    active_key = get_next_api_key()
    if not active_key:
        raise HTTPException(status_code=500, detail="Server Configuration Error: No Gemini API keys configured")

    prompt = f"Translate the following text from {req.src_lang} to {req.target_lang}. Return only the translation:\n{req.text}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={active_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts:
                    translated_text = parts[0].get('text', '').strip()

                    # შედეგის შენახვა Redis-ში (7 დღით = 604800 წამი)
                    if redis_client and translated_text:
                        try:
                            redis_client.setex(cache_key, 604800, translated_text)
                        except Exception as e:
                            print("Redis-ში ჩაწერის შეცდომა:", e)

                    return {"result": translated_text, "source": "ai_engine"}

            raise HTTPException(status_code=502, detail="AI Engine returned empty response")
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Gemini API Error: {response.text}")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI Engine request timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
