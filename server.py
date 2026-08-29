import os
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx

app = FastAPI(title="LingoLens Proxy Backend", version="1.0.0")

# Custom Swagger UI HTML with Vercel Speed Insights
def custom_swagger_ui_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LingoLens Proxy Backend - API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png">
        
        <!-- Vercel Speed Insights -->
        <script>
            window.si = window.si || function () { (window.siq = window.siq || []).push(arguments); };
        </script>
        <script defer src="/_vercel/speed-insights/script.js"></script>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            const ui = SwaggerUIBundle({
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                deepLinking: true
            })
        </script>
    </body>
    </html>
    """

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return HTMLResponse(content=custom_swagger_ui_html())

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

    # Gemini API-სთან უსაფრთხო კავშირი სერვერის მხრიდან
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"Translate text from {req.source_lang} to {req.target_lang}: '{req.text}'"
    if req.mode == "grammar":
        prompt += ". Also provide a short grammar analysis in Georgian."

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=8.0)
            if response.status_code == 200:
                data = response.json()
                result_text = data['candidates'][0]['content']['parts'][0]['text']
                return {
                    "translated_text": result_text,
                    "grammar_analysis": "ანალიზი დასრულებულია." if req.mode == "grammar" else ""
                }
            else:
                raise HTTPException(status_code=500, detail="AI სერვისის შეცდომა")
        except Exception as e:
            raise HTTPException(status_code=504, detail=f"ტაიმაუტის შეცდომა: {str(e)}")
