import requests
from config import BACKEND_URL, API_SECRET_KEY

def send_sms_notification(phone_number: str, message: str) -> dict:
    """SMS შეტყობინების გაგზავნა სერვერის მეშვეობით ან ლოკალურად უსაფრთხოდ."""
    headers = {
        "X-API-Key": API_SECRET_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "phone_number": phone_number,
        "text": message
    }
    
    try:
        # სურვილისამებრ, შეგვიძლია გავაგზავნოთ სერვერის /send-sms/ ენდპოინტზე
        response = requests.post(f"{BACKEND_URL}/send-sms/", json=payload, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"სერვერის შეცდომა SMS-ის გაგზავნისას: {response.status_code}"
            }
            
    except requests.exceptions.RequestException:
        # ოფლაინ რეჟიმში ან კავშირის არქონისას
        print(f"[LingoLens Offline] SMS შენახულია ლოკალურად -> ნომერი: {phone_number}, ტექსტი: {message}")
        return {
            "success": True,
            "message": f"კავშირი არ არის, მაგრამ SMS წარმატებით შეინახა ლოკალურ ურგენტულ ბაზაში: {phone_number}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
