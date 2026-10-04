import requests
from config import BACKEND_URL

class ChatService:
    @staticmethod
    def send_message(prompt, history=None):
        """ აგზავნის შეტყობინებას AI ჩატში და აბრუნებს პასუხს """
        try:
            payload = {"prompt": prompt, "history": history or []}
            response = requests.post(f"{BACKEND_URL}/chat/", json=payload, timeout=6)
            if response.status_code == 200:
                return response.json().get('response', '')
        except Exception as e:
            print(f"Chat Error: {e}")
        return "სერვერთან კავშირის შეცდომა."
