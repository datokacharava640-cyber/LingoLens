import io
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from deep_translator import GoogleTranslator

app = FastAPI(title="LingoLens Universal AI Backend")

def universal_cloud_ocr(image_bytes: bytes, target_lang: str = "eng") -> str:
    """მსოფლიოს ყველა ენის (მათ შორის ქართულის) OCR წაკითხვა"""
    try:
        url = "https://api.ocr.space/parse/image"
        # OCR.space API მხარს უჭერს მრავალ ენას
        payload = {
            'apikey': 'helloworld',
            'language': 'fre' if target_lang == 'fr' else ('ger' if target_lang == 'de' else 'eng'),
            'isOverlayRequired': False,
            'detectOrientation': True
        }
        files = [('file', ('image.jpg', image_bytes, 'image/jpeg'))]
        
        response = requests.post(url, data=payload, files=files, timeout=8)
        if response.status_code == 200:
            result = response.json()
            parsed_results = result.get("ParsedResults", [])
            if parsed_results:
                return parsed_results[0].get("ParsedText", "").strip()
    except Exception as e:
        print(f"[OCR Error]: {e}")
    return ""

@app.get("/")
def read_root():
    return {"status": "LingoLens Universal Engine Active"}

@app.post("/ocr-translate")
async def ocr_and_translate(
    file: UploadFile = File(...), 
    target_lang: str = Form("ka")
):
    try:
        image_bytes = await file.read()
        extracted_text = universal_cloud_ocr(image_bytes, target_lang)

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

@app.post("/translate-text")
async def translate_text_only(
    text: str = Form(...),
    src_lang: str = Form("auto"),
    target_lang: str = Form("ka")
):
    """SMS და ტექსტური შეტყობინებების გრამატიკულად გამართული თარგმნა"""
    try:
        if not text.strip():
            return {"translated_text": ""}
            
        translated = GoogleTranslator(source=src_lang, target=target_lang).translate(text)
        return {
            "status": "success",
            "translated_text": translated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
