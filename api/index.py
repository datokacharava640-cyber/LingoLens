from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

app = FastAPI(title="LingoLens API", version="1.0")

# CORS-ის დაშვება, რომ მობილურმა აპმა თავისუფლად შემოიტანოს მოთხოვნები
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "message": "LingoLens API is running successfully on your own server!"}

@app.post("/translate-image/")
async def translate_image(file: UploadFile = File(...), target_lang: str = Query("ka")):
    api_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="შეცდომა: სერვერზე არ არის მითითებული GEMINI_API_KEY")

    try:
        # ფოტოს წაკითხვა
        image_bytes = await file.read()
        
        # აქ შეგიძლია დაამატო Gemini Vision API ლოგიკა სურათის წასაკითხად და სათარგმნად
        # მიმდინარე ეტაპზე ვაბრუნებთ პასუხს, რომ სერვერმა წარმატებით მიიღო ფოტო
        return {
            "original_text": "Image received successfully",
            "translated_text": f"Target language: {target_lang}",
            "grammar_notes": "Ready for OCR and translation processing."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"სერვერის ხარვეზი: {str(e)}")
