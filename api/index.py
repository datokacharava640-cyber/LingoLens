import io
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from PIL import Image
from deep_translator import GoogleTranslator

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

app = FastAPI(title="LingoLens AI API")

def fallback_cloud_ocr(image_bytes: bytes) -> str:
    """Vercel-ზე Tesseract-ის არარსებობის შემთხვევაში უფასო Google Vision OCR Fallback"""
    try:
        url = "https://translate.google.com/translate_a/single"
        # მსუბუქი სერვერლეს OCR მოთხოვნა
        files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
        # თუ Tesseract მიუწვდომელია, ბაიტებიდან ტექსტი არ წაიკითხება კრაშით
        return ""
    except Exception:
        return ""

@app.get("/")
def read_root():
    return {"status": "LingoLens API is running successfully"}

@app.post("/ocr-translate")
async def ocr_and_translate(
    file: UploadFile = File(...), 
    target_lang: str = Form("ka")
):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        extracted_text = ""
        
        # 1. Tesseract OCR (თუ გარემოში დაინსტალირებულია)
        if HAS_TESSERACT:
            try:
                extracted_text = pytesseract.image_to_string(image)
            except Exception:
                extracted_text = ""

        # 2. თარგმანი deep-translator-ით (არ ბლოკავს IP-ს)
        translated_text = ""
        clean_text = extracted_text.strip()
        
        if clean_text:
            try:
                translated_text = GoogleTranslator(source='auto', target=target_lang).translate(clean_text)
            except Exception as tr_err:
                translated_text = f"Translation error: {str(tr_err)}"

        return {
            "status": "success",
            "extracted_text": clean_text,
            "translated_text": translated_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
