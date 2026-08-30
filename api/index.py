from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel
import os
import httpx
import base64
import json

app = FastAPI()

# Environment Variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION = os.getenv("AZURE_REGION", "eastus")

class TranslateReq(BaseModel):
    text: str
    source_lang: str
    target_lang: str
    mode: str = "standard"

@app.get("/")
def home():
    return {"status": "LingoLens Serverless API Running"}

# --- 1. ტექსტური თარგმნა და გრამატიკა ---
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

# --- 2. ქართული და უცხოური ხმოვანი აუდიოს ამოცნობა (Gemini Multimodal STT) ---
@app.post("/api/audio-translate")
async def process_audio_speech(
    file: UploadFile = File(...),
    source_lang: str = Form("ka"),
    target_lang: str = Form("en_US")
):
    """
    იღებს ტელეფონიდან ჩაწერილ აუდიო ფაილს, გარდაქმნის ტექსტად და აბრუნებს თარგმანს
    """
    if not GEMINI_API_KEY:
        return {"original_text": "ტესტური აუდიო", "translated_text": "Test Audio"}

    try:
        audio_bytes = await file.read()
        base64_audio = base64.b64encode(audio_bytes).decode('utf-8')

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        prompt = (
            f"Listen to the audio. Transcribe it in {source_lang} and translate it to {target_lang}. "
            "Respond ONLY with a valid JSON object with keys 'original' and 'translated'."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
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
            raw_response = data['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # JSON-ის გაპარსვა პასუხიდან
            try:
                cleaned_json = raw_response.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(cleaned_json)
                return {
                    "original_text": parsed.get("original", ""),
                    "translated_text": parsed.get("translated", "")
                }
            except Exception:
                return {
                    "original_text": raw_response,
                    "translated_text": raw_response
                }

    except Exception as e:
        return {"error": f"Audio processing failed: {str(e)}"}

# --- 3. სუფთა ნეირონული გაჟღერება (Azure Neural Georgian TTS) ---
@app.post("/api/tts")
async def text_to_speech_georgian(text: str = Form(...), voice: str = Form("ka-GE-EkaNeural")):
    """
    აგენერირებს სუფთა, ბუნებრივ ქართულ ხმას Microsoft Azure Speech API-ს მეშვეობით
    """
    if not AZURE_SPEECH_KEY:
        # თუ Azure Key არ არის მითითებული, Fallback-ად აბრუნებს შეცდომას
        raise HTTPException(status_code=500, detail="AZURE_SPEECH_KEY is missing in Vercel environment variables")

    url = f"https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
    }

    ssml = f"""
    <speak version='1.0' xml:lang='ka-GE'>
        <voice xml:lang='ka-GE' xml:gender='Female' name='{voice}'>
            {text}
        </voice>
    </speak>
    """

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, headers=headers, content=ssml.encode('utf-8'), timeout=10.0)
            if res.status_code == 200:
                return Response(content=res.content, media_type="audio/mpeg")
            else:
                raise HTTPException(status_code=res.status_code, detail=f"Azure TTS failed: {res.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
