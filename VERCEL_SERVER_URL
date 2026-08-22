from http.server import BaseHTTPRequestHandler
import json
import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        prompt = f"Translate the following text from {data['source_lang']} to {data['target_lang']}. Provide only the translation:\n\n{data['text']}"
        response = model.generate_content(prompt)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'translated_text': response.text.strip()}).encode('utf-8'))
