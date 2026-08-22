from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI()

# API Key ინახება მხოლოდ სერვერის Environment Variable-ში
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

@app.post("/translate")
async def translate(req: TranslateRequest):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Translate from {req.source_lang} to {req.target_lang}:\n{req.text}"
    response = model.generate_content(prompt)
    return {"translated_text": response.text.strip()}
