import io
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from PIL import Image
from deep_translator import GoogleTranslator

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

app = FastAPI(title="LingoLens AI API")

@app.get("/")
def read_root():
    return {"status": "LingoLens API is running successfully"}

@app.post("/ocr-translate")
async def ocr_and_translate(file: UploadFile = File(...), target_lang: str = "ka"):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        extracted_text = ""
        if HAS_TESSERACT:
            try:
                extracted_text = pytesseract.image_to_string(image)
            except Exception:
                extracted_text = ""

        translated = ""
        if extracted_text.strip():
            translated = GoogleTranslator(source='auto', target=target_lang).translate(extracted_text)
            
        return {
            "status": "success",
            "extracted_text": extracted_text.strip(),
            "translated_text": translated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
