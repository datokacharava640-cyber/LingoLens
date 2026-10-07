# sms_service.py
from config import APP_NAME, API_SECRET_KEY

def send_sms_notification(phone_number: str, message: str) -> dict:
    try:
        # აქ იწერება SMS გეითვეის ინტეგრაციის კოდი (მაგ: Twilio API), რომელიც იყენებს config-ის პარამეტრებს
        # მაგალითისთვის ვაბრუნებთ წარმატების პასუხს
        print(f"[{APP_NAME}] SMS გაგზავნა -> ნომერი: {phone_number}, ტექსტი: {message}")
        
        return {
            "success": True,
            "message": f"SMS წარმატებით გაიგზავნა ნომერზე: {phone_number}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
