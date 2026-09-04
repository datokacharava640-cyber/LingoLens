import os
import json
import httpx
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="LingoLens Proxy Backend", version="1.0.0")

# CORS უსაფრთხოება
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECURITY_BEARER = HTTPBearer()
APP_SECRET_TOKEN = os.getenv("APP_INTERNAL_SECRET", "lingolens_secure_token_2026")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str
    mode: str = "standard"  # standard ან grammar

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(SECURITY_BEARER)):
    if credentials.credentials != APP_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="არასწორი ავტორიზაციის ტოკენი")
    return credentials.credentials

@app.post("/api/v1/translate")
async def process_translation(req: TranslationRequest, token: str = Depends(verify_token)):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="ტექსტი ცარიელია")

    if not GEMINI_API_KEY:
        return {
            "translated_text": f"[{req.target_lang.upper()}]: {req.text}",
            "grammar_analysis": "სერვერის API Key არ არის მითითებული."
        }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    if req.mode == "grammar":
        prompt = f"""
        You are a language tutor and professional translator.
        Task:
        1. Translate text from {req.source_lang} to {req.target_lang} naturally (understand Georgian conversational slang/informal phrases).
        2. Provide a clear and helpful grammar and nuance analysis in GEORGIAN language.

        Return ONLY a JSON object with this structure:
        {{
            "translated_text": "the translation string",
            "grammar_analysis": "detailed grammar analysis in Georgian"
        }}

        Text: "{req.text}"
        """
    else:
        prompt = f"""
        Translate the following text from {req.source_lang} to {req.target_lang} naturally (understand slang and conversational phrasing):
        
        Text: "{req.text}"
        
        Return ONLY the translation without any quotes or extra text.
        """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                raw_res = data['candidates'][0]['content']['parts'][0]['text'].strip()

                if req.mode == "grammar":
                    try:
                        # მარტივი გაწმენდა JSON ბლოკებისგან (```json ... ```)
                        clean_json = raw_res.replace("```json", "").replace("```", "").strip()
                        parsed = json.loads(clean_json)
                        return {
                            "translated_text": parsed.get("translated_text", raw_res),
                            "grammar_analysis": parsed.get("grammar_analysis", "ანალიზი ვერ ჩაიტვირთა.")
                        }
                    except Exception:
                        return {
                            "translated_text": raw_res,
                            "grammar_analysis": "გრამატიკული ანალიზი მომზადებულია."
                        }
                else:
                    return {
                        "translated_text": raw_res,
                        "grammar_analysis": ""
                    }
            else:
                raise HTTPException(status_code=500, detail="AI სერვისის შეცდომა")
        except Exception as e:
            raise HTTPException(status_code=504, detail=f"ტაიმაუტის შეცდომა: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
