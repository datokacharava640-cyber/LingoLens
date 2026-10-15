from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "თქვენი_AIZASY_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

class TranslationRequest(BaseModel):
    message: str
    target_lang: str
    history: list = []

@app.post("/api/translate")
async def translate_ai(req: TranslationRequest):
    prompt = (
        f"You are LingoLens AI, a world-class translation and conversation system. "
        f"Translate the user input accurately to {req.target_lang}, "
        f"and provide a natural conversation response in {req.target_lang} with Georgian translation.\n\n"
        f"History:\n" + "\n".join(req.history[-4:]) + f"\n\nInput: {req.message}"
    )
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(GEMINI_URL, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            response_text = data['candidates'][0]['content']['parts'][0]['text']
            return {"status": "success", "response": response_text}
        else:
            raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
