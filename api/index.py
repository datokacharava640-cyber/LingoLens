from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            mode = data.get("mode", "standard")
            source_lang = data.get("source_lang", "ka")
            target_lang = data.get("target_lang", "en_US")
            
            translated_text = ""
            grammar_analysis = ""

            if mode == "vision_ar" and "image_data" in data:
                # Vision OCR/AR Mode via Gemini Vision
                prompt = f"Extract any visible text in this image and translate it directly from {source_lang} to {target_lang}. Return ONLY the target translated text."
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": data["image_data"]}}
                        ]
                    }]
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req) as response:
                    res_json = json.loads(response.read().decode('utf-8'))
                    translated_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()

            elif mode == "grammar":
                # Grammar Analysis Mode
                text = data.get("text", "")
                prompt = f"Translate '{text}' from {source_lang} to {target_lang}. Also provide a brief grammar analysis. Return JSON format: {{\"translated_text\": \"...\", \"grammar_analysis\": \"...\"}}"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req) as response:
                    res_json = json.loads(response.read().decode('utf-8'))
                    raw_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                    try:
                        parsed = json.loads(raw_text.replace("```json", "").replace("```", "").strip())
                        translated_text = parsed.get("translated_text", "")
                        grammar_analysis = parsed.get("grammar_analysis", "")
                    except Exception:
                        translated_text = raw_text

            else:
                # Fast Standard Translation Mode
                text = data.get("text", "")
                prompt = f"Translate the following text accurately from {source_lang} to {target_lang}. Return ONLY the direct translation without extra commentary:\n{text}"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req) as response:
                    res_json = json.loads(response.read().decode('utf-8'))
                    translated_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()

            response_payload = {
                "translated_text": translated_text,
                "grammar_analysis": grammar_analysis,
                "status": "success"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_payload).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
