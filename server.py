import os
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
        # Fallback რეჟიმი თუ სერვერზე API Key არ არის კონფიგურირებული
        return {
            "translated_text": f"[{req.target_lang.upper()}]: {req.text}",
            "grammar_analysis": "სერვერის API Key არ არის მითითებული."
        }

    # Gemini API-სთან უსაფრთხო კავშირი
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # გაუმჯობესებული პრომპტი კონტექსტისა და ჟარგონის სწორი აღქმისთვის
    system_instruction = (
        "You are a professional natural translator. "
        "Translate the input text naturally into the target language. "
        "Pay attention to slang, informal spoken phrasing, and missing punctuation (e.g. understand conversational Georgian phrases like 'რას შვები' accurately as 'what are you doing'). "
        "Return ONLY the direct translation without intro or commentary."
    )
    
    prompt = f"Source Language: {req.source_lang}\nTarget Language: {req.target_lang}\nText to translate: '{req.text}'"
    
    if req.mode == "grammar":
        prompt += "\n\nProvide the natural translation first, followed by a brief grammar and nuance analysis in Georgian."

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_instruction}\n\n{prompt}"}
                ]
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                result_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                
                grammar_info = ""
                if req.mode == "grammar":
                    grammar_info = "ანალიზი დასრულებულია."

                return {
                    "translated_text": result_text,
                    "grammar_analysis": grammar_info
                }
            else:
                raise HTTPException(status_code=500, detail="AI სერვისის შეცდომა")
        except Exception as e:
            raise HTTPException(status_code=504, detail=f"ტაიმაუტის შეცდომა: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
