import os
import json
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="LingoLens Secure Proxy")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

class TextRequest(BaseModel):
    text: str

class ImageRequest(BaseModel):
    image_b64: str

@app.post("/translate")
def translate_text(req: TextRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Server API Key is not configured.")
    
    prompt = (
        "Translate the following text accurately between Georgian and English.\n"
        "Return ONLY a JSON object with key 'translation'.\n"
        f"Text: {req.text}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    
    res = requests.post(f"{GEMINI_URL}?key={GEMINI_API_KEY}", json=payload, timeout=10)
    if res.status_code == 200:
        raw = res.json()['candidates'][0]['content']['parts'][0]['text']
        return json.loads(raw.strip())
    raise HTTPException(status_code=res.status_code, detail="Gemini API Error")

@app.post("/translate-image")
def translate_image(req: ImageRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Server API Key is not configured.")

    prompt = "Extract text from this image and translate it to Georgian/English. Return ONLY JSON with key 'translation'."
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": req.image_b64}}
            ]
        }],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    
    res = requests.post(f"{GEMINI_URL}?key={GEMINI_API_KEY}", json=payload, timeout=15)
    if res.status_code == 200:
        raw = res.json()['candidates'][0]['content']['parts'][0]['text']
        return json.loads(raw.strip())
    raise HTTPException(status_code=res.status_code, detail="OCR Error")
