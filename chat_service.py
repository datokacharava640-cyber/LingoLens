import requests
from config import BACKEND_URL, API_SECRET_KEY

class ChatService:
    @staticmethod
    def send_message(prompt, history=None):
        """ აგზავნის შეტყობინებას AI ჩატში და აბრუნებს პასუხს უსაფრთხოების ჰედერთან ერთად """
        try:
            # სერვერთან თავსებადობისთვის ვუგზავნით 'message' პარამეტრს
            payload = {"message": prompt, "history": history or []}
            headers = {
                "X-API-Key": API_SECRET_KEY,
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/chat/", 
                json=payload, 
                headers=headers, 
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                # ვითვალისწინებთ სერვერის სხვადასხვა შესაძლო პასუხის ფორმატს
                return data.get('response', data.get('message', data.get('translation', 'პასუხი ცარიელია.')))
            else:
                return f"სერვერის შეცდომა: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "სერვერი გამორთულია ან მიუწვდომელია (Connection Error)."
        except requests.exceptions.Timeout:
            return "სერვერმა პასუხი დააგვიანა (Timeout)."
        except Exception as e:
            print(f"Chat Error: {e}")
            return "სერვერთან კავშირის შეცდომა."
