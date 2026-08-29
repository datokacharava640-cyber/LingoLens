from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class TranslateReq(BaseModel):
    text: str
    source_lang: str
    target_lang: str

@app.get("/")
def home():
    return {"status": "LingoLens Serverless API Running"}

@app.post("/api/translate")
async def translate_text(req: TranslateReq):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    if not GEMINI_API_KEY:
        # Fallback პასუხი თუ API KEY ჯერ არ არის დაყენებული Vercel-ის Environment Variables-ში
        return {"translated_text": f"[{req.target_lang.upper()}]: {req.text}"}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"Translate accurately from {req.source_lang} to {req.target_lang}: '{req.text}'"

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=8.0)
            data = res.json()
            translated = data['candidates'][0]['content']['parts'][0]['text']
            return {"translated_text": translated}
        except Exception as e:
            return {"translated_text": f"Error: {str(e)}"}
