import requests
from config import BACKEND_URL, API_SECRET_KEY

class OCRService:
    @staticmethod
    def recognize_image(image_path):
        """ აგზავნის სურათს სერვერზე OCR-ისთვის და აბრუნებს ტექსტს """
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                headers = {"X-API-Key": API_SECRET_KEY} if 'API_SECRET_KEY' in globals() and API_SECRET_KEY else {}
                
                response = requests.post(
                    f"{BACKEND_URL}/ocr/", 
                    files=files, 
                    headers=headers, 
                    timeout=5
                )
                
                if response.status_code == 200:
                    return response.json().get('text', '')
                else:
                    return f"სერვერის შეცდომა: {response.status_code}"
                    
        except Exception as e:
            print(f"OCR Error: {e}")
            return "ვერ მოხერხდა ტექსტის ამოცნობა."
