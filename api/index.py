from http.server import BaseHTTPRequestHandler
import json
import os
import requests

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        response_data = {"status": "online", "message": "LingoLens API is running successfully!"}
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            prompt = body.get('prompt', '')
            api_key = os.environ.get('GEMINI_API_KEY', '')

            if not api_key:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"result": "შეცდომა: GEMINI_API_KEY ვერ მოიძებნა"}, ensure_ascii=False).encode('utf-8'))
                return

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            headers = {"Content-Type": "application/json"}

            res = requests.post(url, json=payload, headers=headers, timeout=15)
            res_data = res.json()

            translated_text = ""
            if "candidates" in res_data and len(res_data["candidates"]) > 0:
                parts = res_data["candidates"][0].get("content", {}).get("parts", [])
                if parts:
                    translated_text = parts[0].get("text", "")

            if not translated_text:
                translated_text = "ვერ მოხერხდა თარგმნა (ცარიელი პასუხი)"

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            # ვაბრუნებთ როგორც "result"-ში, ისე პირდაპირ ტექსტად სტაბილურობისთვის
            self.wfile.write(json.dumps({"result": translated_text}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(200) # ვუგზავნით 200-ს, რომ აპმა შეცდომა არ აჩვენოს
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"result": f"სერვერის ხარვეზი: {str(e)}"}, ensure_ascii=False).encode('utf-8'))
