from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import httpx

app = FastAPI()

# Custom Swagger UI HTML with Vercel Speed Insights
def custom_swagger_ui_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LingoLens API - Documentation</title>
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
