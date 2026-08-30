from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import os
import httpx

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class TranslateReq(BaseModel):
    text: str
    source_lang: str
    target_lang: str
    mode: str = "standard"

@app.get("/")
def home():
    return {"status": "LingoLens Serverless API Running"}

@app.post("/api/translate")
@app.post("/api/index")
async def translate_text(req: TranslateReq):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    if not GEMINI_API_KEY:
        return {"translated_text": f"[{req.target_lang.upper()}]: {req.text}"}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    if req.mode == "grammar":
        prompt = f"Translate from {req.source_lang} to {req.target_lang}: '{req.text}'. Also analyze the grammar briefly in Georgian."
    else:
        prompt = f"Translate accurately from {req.source_lang} to {req.target_lang}. Return ONLY the final translated text without any explanation: '{req.text}'"

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=8.0)
            data = res.json()
            translated = data['candidates'][0]['content']['parts'][0]['text'].strip()
            
            if req.mode == "grammar":
                return {
                    "translated_text": translated,
                    "grammar_analysis": "გრამატიკული ანალიზი შესრულებულია Gemini AI-ს მიერ."
                }
            return {"translated_text": translated}
        except Exception as e:
            return {"translated_text": f"Error: {str(e)}"}

# --- ქართული და უცხოური ხმოვანი აუდიოს დამუშავება (Whisper STT Integration) ---
@app.post("/api/audio-translate")
async def process_audio_speech(
    file: UploadFile = File(...),
    source_lang: str = Form("ka"),
    target_lang: str = Form("en_US")
):
    """
    იღებს ტელეფონიდან ჩაწერილ აუდიო ფაილს, გარდაქმნის ტექსტად (Whisper/Gemini-ით) და აბრუნებს თარგმანს
    """
    if not GEMINI_API_KEY:
        return {"original_text": "ტესტური აუდიო", "translated_text": "Test Audio"}

    try:
        audio_bytes = await file.read()
        
        # Gemini Multimodal API-ს გამოძახება პირდაპირი აუდიო ფაილის ამოცნობისთვის
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        import base64
        base64_audio = base64.b64encode(audio_bytes).decode('utf-8')

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"Transcribe the audio accurately in its original language ({source_lang}), and then translate it to {target_lang}. Format response as JSON with keys 'original' and 'translated'."
                        },
                        {
                            "inline_data": {
                                "mime_type": file.content_type or "audio/wav",
                                "data": base64_audio
                            }
                        }
                    ]
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, timeout=12.0)
            data = res.json()
            result_text = data['candidates'][0]['content']['parts'][0]['text']
            
            return {
                "original_text": result_text,
                "translated_text": result_text
            }
    except Exception as e:
        return {"error": f"Audio processing failed: {str(e)}"}
