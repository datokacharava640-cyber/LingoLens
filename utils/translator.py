import json
import threading
import urllib.request

def translate_text(prompt, text, src_lang, target_lang, callback):
    def worker():
        try:
            url = "http://37.27.255.1:8000/translate"
            payload = json.dumps({
                "text": text,
                "source": src_lang,
                "target": target_lang,
                "prompt": prompt
            }).encode("utf-8")
            
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                result_text = (
                    res_data.get("translated_text")
                    or res_data.get("result")
                    or str(res_data)
                )
                callback(result_text)
        except Exception as e:
            print("Translation Server Error:", e)
            callback(None)

    threading.Thread(target=worker, daemon=True).start()
