import requests
from config import BACKEND_URL

class OCRService:
    @staticmethod
    def recognize_image(image_path):
        """ აგზავნის სურათს სერვერზე OCR-ისთვის და აბრუნებს ტექსტს """
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{BACKEND_URL}/ocr/", files=files, timeout=5)
                if response.status_code == 200:
                    return response.json().get('text', '')
        except Exception as e:
            print(f"OCR Error: {e}")
        return "ვერ მოხერხდა ტექსტის ამოცნობა."
