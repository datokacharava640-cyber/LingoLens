import io
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from deep_translator import GoogleTranslator

app = FastAPI(title="LingoLens Production API")

def robust_cloud_ocr(image_bytes: bytes) -> str:
    """უზრუნველყოფს კამერიდან ტექსტის ამოცნობას შეფერხების გარეშე"""
    try:
        url = "https://api.ocr.space/parse/image"
        files = [('file', ('image.jpg', image_bytes, 'image/jpeg'))]
        data = {
            'apikey': 'helloworld',
            'language': 'eng',
            'isOverlayRequired': False,
            'OCREngine': '2'  # Engine 2 უფრო ზუსტია ლათინური და ციფრული ტექსტებისთვის
        }
        res = requests.post(url, files=files, data=data, timeout=8)
        if res.status_code == 200:
            parsed = res.json().get("ParsedResults", [])
            if parsed:
                return parsed[0].get("ParsedText", "").strip()
    except Exception as e:
        print(f"[OCR Error]: {e}")
    return ""

@app.get("/")
def root():
    return {"status": "LingoLens Server Running"}

@app.post("/ocr-translate")
async def ocr_and_translate(
    file: UploadFile = File(...), 
    target_lang: str = Form("ka")
):
    try:
        image_bytes = await file.read()
        extracted = robust_cloud_ocr(image_bytes)

        translated = ""
        if extracted:
            translated = GoogleTranslator(source='auto', target=target_lang).translate(extracted)

        return {
            "status": "success",
            "extracted_text": extracted,
            "translated_text": translated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate-text")
async def translate_text(
    text: str = Form(...),
    src_lang: str = Form("auto"),
    target_lang: str = Form("ka")
):
    try:
        if not text.strip():
            return {"translated_text": ""}
        translated = GoogleTranslator(source=src_lang, target=target_lang).translate(text)
        return {"status": "success", "translated_text": translated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
