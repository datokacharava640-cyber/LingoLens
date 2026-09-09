import io
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from deep_translator import GoogleTranslator

app = FastAPI(title="LingoLens Cloud OCR API")

def free_cloud_ocr(image_bytes: bytes) -> str:
    """ტექსტის ამოცნობა უფასო Cloud OCR API-ს საშუალებით"""
    try:
        url = "https://api.ocr.space/parse/image"
        payload = {'apikey': 'helloworld', 'language': 'eng'}
        files = [('file', ('image.jpg', image_bytes, 'image/jpeg'))]
        
        response = requests.post(url, data=payload, files=files, timeout=6)
        if response.status_code == 200:
            result = response.json()
            parsed_results = result.get("ParsedResults", [])
            if parsed_results:
                return parsed_results[0].get("ParsedText", "").strip()
    except Exception as e:
        print(f"[OCR Cloud Error]: {e}")
    return ""

@app.get("/")
def read_root():
    return {"status": "LingoLens Cloud API Active"}

@app.post("/ocr-translate")
async def ocr_and_translate(
    file: UploadFile = File(...), 
    target_lang: str = Form("ka")
):
    try:
        image_bytes = await file.read()
        
        # 1. ტექსტის ამოცნობა Cloud OCR-ით
        extracted_text = free_cloud_ocr(image_bytes)

        # 2. ამოცნობილი ტექსტის თარგმნა
        translated_text = ""
        if extracted_text:
            try:
                translated_text = GoogleTranslator(source='auto', target=target_lang).translate(extracted_text)
            except Exception as tr_err:
                translated_text = str(tr_err)

        return {
            "status": "success",
            "extracted_text": extracted_text,
            "translated_text": translated_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
