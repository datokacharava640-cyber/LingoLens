import requests
from config import API_ENDPOINT, API_SECRET_KEY

def send_image_to_server_for_ocr(image_path: str, source_lang: str = "eng", target_lang: str = "ka"):
    """ფოტოს გაგზავნა სერვერზე OCR-ისა და თარგმნისთვის უსაფრთხოების ჰედერთან ერთად."""
    headers = {
        "X-API-Key": API_SECRET_KEY
    }
    
    try:
        with open(image_path, "rb") as img_file:
            files = {"file": img_file}
            data = {"source_lang": source_lang, "target_lang": target_lang}
            
            # მოთხოვნა სერვერთან 10 წამიანი ლიმიტით
            response = requests.post(API_ENDPOINT, files=files, data=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"სერვერის შეცდომა: {response.status_code}"}
                
    except requests.exceptions.RequestException:
        # როცა ინტერნეტი ან სერვერი არ არის ხელმისაწვდომი
        return {"success": False, "error": "კავშირი არ არის ინტერნეტთან ან სერვერთან!"}
    except Exception as e:
        return {"success": False, "error": str(e)}
