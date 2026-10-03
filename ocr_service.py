import pytesseract
from PIL import Image
import io
from config import APP_NAME, BACKEND_URL

def process_image_ocr(contents: bytes, source_lang: str, target_lang: str) -> dict:
    try:
        # სურათის გახსნა ბაიტებიდან
        image = Image.open(io.BytesIO(contents))
        
        # Pytesseract-ის გამოყენებით ტექსტის ამოცნობა
        extracted_text = pytesseract.image_to_string(image, config='--psm 6')
        
        # ტექსტის თარგმანის სიმულაცია/დამუშავება
        translated_text = f"[{APP_NAME} თარგმანი ({source_lang} -> {target_lang})]: {extracted_text.strip()}"
        
        return {
            "success": True,
            "original_text": extracted_text.strip(),
            "translated_text": translated_text,
            "service_backend": BACKEND_URL
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
