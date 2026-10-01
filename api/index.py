import threading
import requests
from config import API_ENDPOINT, API_SECRET_KEY


def send_data_to_server(payload_data: dict, callback=None):
    """სერვერთან უსაფრთხო კომუნიკაცია API Key-ის გამოყენებით (ასინქრონული, ფონურ ნაკადში)."""
    def background_task():
        headers = {
            "X-API-Key": API_SECRET_KEY,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                API_ENDPOINT, json=payload_data, headers=headers, timeout=5
            )
            if response.status_code == 200:
                result = {"success": True, "data": response.json()}
            else:
                result = {
                    "success": False,
                    "error": f"Server error status code: {response.status_code}",
                }
        except requests.exceptions.RequestException as e:
            result = {"success": False, "error": str(e)}

        # თუ გადაცემულია ქოლბექი (callback), შედეგი უბრუნდება მთავარ ნაკადს
        if callback:
            callback(result)

    # თრედის გაშვება იმისათვის, რომ UI ("Loading..." ეკრანი) არ ჩაიჭედოს
    threading.Thread(target=background_task, daemon=True).start()


def check_server_health(callback=None):
    """სერვერის მუშაობის (Health Check) შემოწმება ფონურ რეჟიმში."""
    def background_check():
        try:
            response = requests.get("http://37.27.255.1:8000/", timeout=3)
            is_healthy = (response.status_code == 200)
        except:
            is_healthy = False
            
        if callback:
            callback(is_healthy)

    threading.Thread(target=background_check, daemon=True).start()
