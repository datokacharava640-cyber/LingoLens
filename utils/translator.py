import json
import threading
import urllib.request
import config  # ვრთავთ კონფიგურაციის ფაილს
from kivy.clock import Clock  # ვრთავთ Clock-ს მთავარ ნაკადში გამოსაძახებლად

def translate_text(prompt, text, src_lang, target_lang, callback):
    def worker():
        try:
            # ვიყენებთ კონფიგურაციაში მითითებულ სერვერის მისამართს
            url = f"{getattr(config, 'BACKEND_URL', 'http://37.27.255.1:8000')}/translate"
            
            payload = json.dumps({
                "text": text,
                "source": src_lang,
                "target": target_lang,
                "prompt": prompt
            }).encode("utf-8")
            
            # ვასწორებთ ჰედერს FastAPI-ს სტანდარტზე (X-Api-Key)
            api_key = getattr(config, 'API_SECRET_KEY', '')
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": api_key  
            }
            
            req = urllib.request.Request(
                url,
                data=payload,
                headers=headers,
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                result_text = (
                    res_data.get("translated_text")
                    or res_data.get("result")
                    or str(res_data)
                )
                if callback:
                    # ვუზრუნველყოფთ, რომ UI განახლდეს მთავარ ნაკადში
                    Clock.schedule_once(lambda dt: callback(result_text), 0)
                    
        except Exception as e:
            print("Translation Server Error:", e)
            if callback:
                Clock.schedule_once(lambda dt: callback(None), 0)

    threading.Thread(target=worker, daemon=True).start()


def analyze_image_and_translate(image_path, target_language="ka", callback=None):
    """
    სურათის გაგზავნა სერვერზე OCR-ისა და თარგმანისთვის.
    """
    def worker():
        try:
            url = f"{getattr(config, 'BACKEND_URL', 'http://37.27.255.1:8000')}/api/v1/process"
            
            with open(image_path, "rb") as f:
                image_data = f.read()

            boundary = "BoundaryStringLingoLens"
            headers = {
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "X-Api-Key": getattr(config, 'API_SECRET_KEY', '')  # აქაც ვასწორებთ
            }

            body = (
                f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"target_language\"\r\n\r\n"
                f"{target_language}\r\n"
                f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"image\"; filename=\"captured.png\"\r\n"
                f"Content-Type: image/png\r\n\r\n"
            ).encode("utf-8") + image_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

            req = urllib.request.Request(url, data=body, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                result_text = res_data.get("translated_text", "ვერ მოხერხდა დამუშავება.")
                if callback:
                    Clock.schedule_once(lambda dt: callback(result_text), 0)

        except Exception as e:
            print("Image Analysis Server Error:", e)
            if callback:
                Clock.schedule_once(lambda dt: callback("სერვერთან დაკავშირების ან დამუშავების შეცდომა."), 0)

    threading.Thread(target=worker, daemon=True).start()
