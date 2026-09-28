import requests
import threading
from config import BACKEND_URL, GEMINI_API_KEY, APP_NAME, VERSION

def translate_text(prompt, text, source_language="ka", target_language="en", callback=None):
    """
    ფუნქცია აგზავნის მოთხოვნას სერვერზე ფონურ რეჟიმში (threading), 
    რათა აპლიკაციის ინტერფეისი არ გაიყინოს.
    """
    def background_request():
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"{APP_NAME}/{VERSION}"
        }
        
        payload = {
            "prompt": prompt,
            "text": text,
            "source_language": source_language,
            "target_language": target_language,
            "api_key": GEMINI_API_KEY
        }
        
        try:
            # ვამოწმებთ სერვერის მისამართს - თუ ბოლოში /translate არ წერია, თავად ვამატებთ
            url = BACKEND_URL if BACKEND_URL.endswith("/translate") else f"{BACKEND_URL.rstrip('/')}/translate"
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("translated_text", data.get("result", "თარგმანი ვერ მოიძებნა"))
                if callback:
                    callback(result)
            else:
                if callback:
                    callback(f"სერვერის შეცდომა: {response.status_code}")
                    
        except requests.exceptions.RequestException as e:
            if callback:
                callback(f"კავშირის შეცდომა: {e}")

    # ვუშვებთ ფონურ ნაკადში (Thread)
    threading.Thread(target=background_request, daemon=True).start()

def analyze_image_and_translate(image_path, target_language="ka", callback=None):
    """
    სურათის ანალიზისა და OCR-ის ფუნქცია (საჭიროებისამებრ)
    """
    def background_image_request():
        # აქ შეგიძლია დაამატო სურათის გაგზავნის ლოგიკა შენს სერვერზე
        if callback:
            callback("სურათის ანალიზი მუშავდება სერვერზე...")

    threading.Thread(target=background_image_request, daemon=True).start()

if __name__ == "__main__":
    print(f"მიმდინარეობს ტესტირება - {APP_NAME} v{VERSION}")
