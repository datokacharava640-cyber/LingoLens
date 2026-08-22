from http.server import BaseHTTPRequestHandler
import json
import os
import google.generativeai as genai

# Vercel Environment Variables-ში დაამატე GEMINI_API_KEY
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            source_lang = data.get('source_lang', 'auto')
            target_lang = data.get('target_lang', 'en')
            text = data.get('text', '')

            if not text:
                self._send_response({'error': 'Empty text'}, 400)
                return

            prompt = f"Translate text accurately from {source_lang} to {target_lang}. Return ONLY translated string:\n{text}"
            response = model.generate_content(prompt)
            
            self._send_response({'translated_text': response.text.strip()}, 200)
        except Exception as e:
            self._send_response({'error': str(e)}, 500)

    def _send_response(self, payload, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))
