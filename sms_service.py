# sms_service.py

def send_sms_notification(phone_number: str, message: str) -> dict:
    try:
        # აქ იწერება SMS გეითვეის ინტეგრაციის კოდი (მაგ: Twilio API)
        # მაგალითისთვის ვაბრუნებთ წარმატების პასუხს
        print(to=phone_number, body=message) # სიმულაცია
        
        return {
            "success": True,
            "message": f"SMS წარმატებით გაიგზავნა ნომერზე: {phone_number}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
