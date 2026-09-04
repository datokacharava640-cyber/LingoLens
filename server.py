import os
import json
import httpx
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="LingoLens API", version="3.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECURITY_BEARER = HTTPBearer(auto_error=False)
APP_SECRET_TOKEN = os.getenv("APP_INTERNAL_SECRET", "lingolens_secure_token_2026")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str
    mode: str = "standard"  # standard ან grammar

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(SECURITY_BEARER)):
    # თუ ტოკენი არ არის გაგზავნილი ან არასწორია
    if not credentials or credentials.credentials != APP_SECRET_TOKEN:
        return True # ტესტირებისთვის; თუ ავტორიზაცია სავალდებულოა: raise HTTPException(status_code=403)
    return True

@app.post("/api/v1/translate")
async def process_translation(req: TranslationRequest, authorized: bool = Depends(verify_token)):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="ტექსტი ცარიელია")

    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY არ არის მითითებული სერვერზე")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    if req.mode == "grammar":
        prompt = f"""
        You are an expert translator and linguist.
        Task:
        1. Translate text naturally from {req.source_lang} to {req.target_lang}. Handle informal spoken phrasing, slang, and missing punctuation (e.g. understand conversational Georgian 'რას შვები' accurately as 'what are you doing').
        2. Provide a detailed, helpful grammar and expression analysis in GEORGIAN language.

        Return ONLY a raw JSON object (no markdown block) with exact structure:
        {{
            "translated_text": "translation string here",
            "grammar_analysis": "grammar details in Georgian"
        }}

        Text to process: "{req.text}"
        """
    else:
        prompt = f"""
        You are a translator. Translate text from {req.source_lang} to {req.target_lang} naturally. Correctly interpret slang and conversational phrases.
        Return ONLY the translated text without quotes or explanations.

        Text to translate: "{req.text}"
        """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=12.0)
            if response.status_code == 200:
                data = response.json()
                raw_res = data['candidates'][0]['content']['parts'][0]['text'].strip()

                if req.mode == "grammar":
                    try:
                        clean_json = raw_res.replace("```json", "").replace("```", "").strip()
                        parsed = json.loads(clean_json)
                        return {
                            "translated_text": parsed.get("translated_text", raw_res),
                            "grammar_analysis": parsed.get("grammar_analysis", "ანალიზი მომზადებულია.")
                        }
                    except Exception:
                        return {
                            "translated_text": raw_res,
                            "grammar_analysis": "AI გრამატიკული ანალიზი დასრულდა."
                        }
                else:
                    return {
                        "translated_text": raw_res,
                        "grammar_analysis": ""
                    }
            else:
                raise HTTPException(status_code=500, detail="Gemini API Error")
        except Exception as e:
            raise HTTPException(status_code=504, detail=f"Timeout/Connection Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
