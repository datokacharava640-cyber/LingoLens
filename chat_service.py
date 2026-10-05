import requests
from config import BACKEND_URL, API_SECRET_KEY

class ChatService:
    @staticmethod
    def send_message(prompt, history=None):
        """ აგზავნის შეტყობინებას AI ჩატში და აბრუნებს პასუხს """
        try:
            payload = {"prompt": prompt, "history": history or []}
            headers = {"X-API-Key": API_SECRET_KEY} if 'API_SECRET_KEY' in globals() or API_SECRET_KEY else {}
            
            response = requests.post(
                f"{BACKEND_URL}/chat/", 
                json=payload, 
                headers=headers, 
                timeout=6
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                return f"სერვერის შეცდომა: {response.status_code}"
                
        except Exception as e:
            print(f"Chat Error: {e}")
            return "სერვერთან კავშირის შეცდომა."
