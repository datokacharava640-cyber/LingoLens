import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

@app.post("/api/index")
async def translate(req: TranslateRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set on Vercel")
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            f"You are a professional translator. Translate the following text "
            f"from '{req.source_lang}' to '{req.target_lang}'. "
            f"Output ONLY the translated text, with no additional explanations or quotes.\n\n"
            f"Text: {req.text}"
        )
        response = model.generate_content(prompt)
        return {"translated_text": response.text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
