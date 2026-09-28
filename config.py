import requests
from config import BACKEND_URL, GEMINI_API_KEY, APP_NAME, VERSION

def translate_text(text, target_language="ka"):
    """
    ფუნქცია აგზავნის ტექსტს თარგმნისთვის Vercel სერვერზე ან Gemini API-ში.
    """
    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"{APP_NAME}/{VERSION}"
    }
    
    payload = {
        "text": text,
        "target_language": target_language,
        "api_key": GEMINI_API_KEY
    }
    
    try:
        response = requests.post(BACKEND_URL, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("translated_text", "თარგმანი ვერ მოიძებნა")
        else:
            return f"სერვერის შეცდომა: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"კავშირის შეცდომა: {e}"

if __name__ == "__main__":
    # ტესტირება
    print(f"მიმდინარეობს ტესტირება - {APP_NAME} v{VERSION}")
    # result = translate_text("Hello world", "ka")
    # print(result)
