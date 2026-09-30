import json
import threading
import urllib.request
import config  # ვრთავთ კონფიგურაციის ფაილს

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
            
            # ვამატებთ საიდუმლო გასაღებს ჰედედერში (თუ სერვერი ითხოვს ავტორიზაციას)
            api_key = getattr(config, 'API_SECRET_KEY', '')
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": api_key  # ან "Authorization": f"Bearer {api_key}" (გააჩნია როგორ ააწყვე სერვერი)
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
                    callback(result_text)
                    
        except Exception as e:
            print("Translation Server Error:", e)
            if callback:
                callback(None)

    threading.Thread(target=worker, daemon=True).start()


def analyze_image_and_translate(image_path, target_language="ka", callback=None):
    """
    სურათის გაგზავნა სერვერზე OCR-ისა და თარგმანისთვის.
    """
    def worker():
        try:
            url = f"{getattr(config, 'BACKEND_URL', 'http://37.27.255.1:8000')}/api/v1/process"
            
            # მულტიპარტ (Multipart/form-data) მოთხოვნის აწყობა urllib-ით სირთულის თავიდან ასაცილებლად 
            # ან მარტივი ბინარული გაგზავნა:
            with open(image_path, "rb") as f:
                image_data = f.read()

            boundary = "BoundaryStringLingoLens"
            headers = {
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "X-API-Key": getattr(config, 'API_SECRET_KEY', '')
            }

            # ვამზადებთ მულტიპარტ σgetBody-ს
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
                    callback(result_text)

        except Exception as e:
            print("Image Analysis Server Error:", e)
            if callback:
                callback("სერვერთან დაკავშირების ან დამუშავების შეცდომა.")

    threading.Thread(target=worker, daemon=True).start()
