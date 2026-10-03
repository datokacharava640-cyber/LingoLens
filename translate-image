import requests
from config import API_ENDPOINT  # ეს არის მაგალითად http://.../translate-image/

def send_image_to_server_for_ocr(image_path: str, source_lang: str = "eng", target_lang: str = "ka"):
    try:
        with open(image_path, "rb") as img_file:
            files = {"file": img_file}
            data = {"source_lang": source_lang, "target_lang": target_lang}
            
            # სერვერთან კომუნიკაცია (არანაირი ტელეფონის რესურსი არ იხარჯება!)
            response = requests.post(API_ENDPOINT, files=files, data=data, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"Server error: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
