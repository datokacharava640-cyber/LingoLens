import io
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from PIL import Image
from deep_translator import GoogleTranslator

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

app = FastAPI(title="LingoLens Live OCR API")

@app.get("/")
def read_root():
    return {"status": "LingoLens Live API is active"}

@app.post("/ocr-translate")
async def ocr_and_translate(file: UploadFile = File(...), target_lang: str = Form("ka")):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        extracted_text = ""
        if HAS_TESSERACT:
            try:
                extracted_text = pytesseract.image_to_string(image)
            except Exception:
                extracted_text = ""

        translated_text = ""
        if extracted_text.strip():
            translated_text = GoogleTranslator(source='auto', target=target_lang).translate(extracted_text)

        return {
            "status": "success",
            "extracted_text": extracted_text.strip(),
            "translated_text": translated_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
