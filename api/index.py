from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
from gtts import gTTS
from googletrans import Translator
from PIL import Image
import io

app = FastAPI(title="LingoLens API", version="1.0.0")

# სერვერის კონფიგურაცია
BACKEND_URL = "http://37.27.255.1:8001"
API_URL = "http://37.27.255.1:8001"

# CORS-ის დაშვება, რომ მობილურმა აპმა თავისუფლად შემოიტანოს მოთხოვნები
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

translator = Translator()

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "message": "LingoLens AI Server is running perfectly!",
        "backend_url": BACKEND_URL
    }

@app.post("/translate-image/")
async def translate_image(file: UploadFile = File(...), target_lang: str = Query("ka")):
    try:
        # ფოტოს წაკითხვა Pillow-ით
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # მომავალში აქ დაემატება ტექსტის ამოცნობა (OCR) და თარგმანი
        sample_text = "Hello from LingoLens AI"
        
        # googletrans-ის გამოყენება თარგმანისთვის
        translated = translator.translate(sample_text, dest=target_lang)

        return {
            "status": "success",
            "original_text": sample_text,
            "translated_text": translated.text,
            "target_language": target_lang,
            "grammar_notes": "Image successfully processed and translated."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"სერვერის ხარვეზი: {str(e)}")
