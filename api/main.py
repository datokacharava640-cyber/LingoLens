from fastapi import FastAPI, UploadFile, File
from PIL import Image
import pytesseract
from deep_translator import GoogleTranslator
import io

app = FastAPI(title="LingoLens AI API")

@app.get("/")
def read_root():
    return {"status": "LingoLens API is running"}

@app.post("/ocr-translate")
async def ocr_and_translate(file: UploadFile = File(...), target_lang: str = "ka"):
    # 1. ფოტოს წაკითხვა
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))
    
    # 2. OCR ტექსტის ამოცნობა
    extracted_text = pytesseract.image_to_string(image)
    
    # 3. თარგმანი
    if extracted_text.strip():
        translated = GoogleTranslator(source='auto', target=target_lang).translate(extracted_text)
    else:
        translated = ""
        
    return {
        "extracted_text": extracted_text.strip(),
        "translated_text": translated
    }
