# lingolens-backend/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import json
import os

app = FastAPI(title="LingoLens Central API")

# 1. Redis ქეშირების ბაზასთან კავშირი
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 2. Multiple API Key Pool (ლიმიტების გადასანაწილებლად)
API_KEYS = [
    os.getenv("GEMINI_KEY_1", "YOUR_KEY_1"),
    os.getenv("GEMINI_KEY_2", "YOUR_KEY_2"),
    os.getenv("GEMINI_KEY_3", "YOUR_KEY_3")
]
current_key_index = 0

def get_next_api_key():
    global current_key_index
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return key

class TranslationRequest(BaseModel):
    text: str
    src_lang: str
    target_lang: str

@app.post("/api/v1/translate")
async def translate(req: TranslationRequest):
    cache_key = f"trans:{req.src_lang}:{req.target_lang}:{req.text.strip().lower()}"
    
    # 3. შემოწმება ქეშში (თუ უკვე ნათარგმნია, გაიცემა მომენტალურად)
    cached_result = redis_client.get(cache_key)
    if cached_result:
        return {"result": cached_result, "source": "cache"}

    # 4. თუ ქეშში არ არის — მოთხოვნა იგზავნება AI-თან (Key Rotation-ით)
    active_key = get_next_api_key()
    
    try:
        # აქ იწერება AI მოთხოვნის ლოგიკა (Gemini ან LLaMA 3)
        translated_text = f"[Translated via LingoLens Server]: {req.text}" # დემო პასუხი
        
        # 5. შედეგის შენახვა ქეშში (მაგ. 7 დღით)
        redis_client.setex(cache_key, 604800, translated_text)
        
        return {"result": translated_text, "source": "ai_engine"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
