from http.server import BaseHTTPRequestHandler
import json
import os
import requests

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        # როდესაც ბრაუზერიდან ან ტესტურად ხსნიან ლინკს, დააბრუნოს სტატუსი
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
                self.wfile.write(json.dumps({"error": "GEMINI_API_KEY ვერ მოიძებნა"}, ensure_ascii=False).encode('utf-8'))
                return

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            headers = {"Content-Type": "application/json"}

            # გავზარდეთ timeout 15 წამამდე სტაბილურობისთვის
            res = requests.post(url, json=payload, headers=headers, timeout=15)
            res_data = res.json()

            translated_text = ""
            if "candidates" in res_data and len(res_data["candidates"]) > 0:
                parts = res_data["candidates"][0].get("content", {}).get("parts", [])
                if parts:
                    translated_text = parts[0].get("text", "")

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"result": translated_text}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode('utf-8'))
