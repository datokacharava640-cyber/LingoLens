import threading
import requests
from kivy.clock import Clock  # აუცილებელია UI-ს უსაფრთხო განახლებისთვის
from config import API_ENDPOINT, API_SECRET_KEY, BACKEND_URL


def send_data_to_server(payload_data: dict, callback=None):
    """სერვერთან უსაფრთხო კომუნიკაცია API Key-ის გამოყენებით (ასინქრონული, ფონურ ნაკადში)."""
    def background_task():
        headers = {
            "X-Api-Key": API_SECRET_KEY,  # FastAPI-სთან სრული თანხვედრისთვის
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

        # შედეგი უბრუნდება მთავარ ნაკადს Clock-ის მეშვეობით
        if callback:
            Clock.schedule_once(lambda dt: callback(result), 0)

    # თრედის გაშვება იმისათვის, რომ UI არ ჩაიჭედოს
    threading.Thread(target=background_task, daemon=True).start()


def check_server_health(callback=None):
    """სერვერის მუშაობის (Health Check) შემოწმება ფონურ რეჟიმში config-იდან წამოღებული URL-ით."""
    def background_check():
        try:
            # ვიყენებთ BACKEND_URL-ს პირდაპირი მითითების ნაცვლად
            response = requests.get(f"{BACKEND_URL}/", timeout=3)
            is_healthy = (response.status_code == 200)
        except:
            is_healthy = False
            
        if callback:
            Clock.schedule_once(lambda dt: callback(is_healthy), 0)

    threading.Thread(target=background_check, daemon=True).start()
