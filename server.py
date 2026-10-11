from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from deep_translator import GoogleTranslator
from gtts import gTTS
import os
import google.generativeai as genai

app = FastAPI(title="LingoLens Gemini Backend", version="4.0")

# 🔑 Google Gemini API კონფიგურაცია
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6JJSsFMn2prUcWLyEJ2rPUACvXTKdaP0A6bFJwhlaqXrw")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "en"

class ChatRequest(BaseModel):
    message: str

class VoiceChatRequest(BaseModel):
    message: str
    lang: str = "ka"

@app.get("/")
def home():
    return {"status": "LingoLens Gemini Server is running!", "version": "4.0"}

@app.post("/translate/")
def translate_text(req: TranslateRequest):
    cleaned_text = req.text.strip()
    if not cleaned_text:
        raise HTTPException(status_code=400, detail="ტექსტი ცარიელია")
    
    try:
        translated_output = GoogleTranslator(source='auto', target=req.target_lang).translate(cleaned_text)
    except Exception as e:
        translated_output = f"ვერ მოხერხდა თარგმნა: {str(e)}"
    
    return {
        "original": cleaned_text,
        "target_lang": req.target_lang,
        "translation": translated_output,
        "status": "success"
    }

@app.post("/chat/")
def chat_ai(req: ChatRequest):
    try:
        # Google Gemini-სთან გაგზავნა
        response = model.generate_content(req.message)
        return {"reply": response.text, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API შეცდომა: {str(e)}")

@app.post("/voice-chat/")
def voice_chat(req: VoiceChatRequest):
    try:
        # 1. პასუხის მიღება Gemini-სგან
        response = model.generate_content(req.message)
        response_text = response.text

        # 2. ხმის გენერაცია gTTS-ით
        audio_filename = "response_audio.mp3"
        tts = gTTS(text=response_text, lang=req.lang, slow=False)
        tts.save(audio_filename)

        return {
            "status": "success",
            "reply_text": response_text,
            "audio_url": f"http://37.27.255.1:8000/audio/{audio_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"შეცდომა: {str(e)}")

@app.get("/audio/{filename}")
def get_audio(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="აუდიო ფაილი ვერ მოიძებნა")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
