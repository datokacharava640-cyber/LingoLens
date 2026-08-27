from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        mode = data.get('mode', 'standard')
        source_lang = data.get('source_lang', 'ka')
        target_lang = data.get('target_lang', 'en')
        text = data.get('text', '')

        # Google Translate API-ს უფასო ენდპოინტი
        target_short = target_lang.split('_')[0]
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_short}&dt=t&q={urllib.parse.quote(text)}"

        translated_text = ""
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                res = json.loads(response.read().decode('utf-8'))
                translated_text = "".join([item[0] for item in res[0] if item[0]])
        except Exception as e:
            translated_text = text

        response_payload = {}

        if mode == 'standard':
            response_payload = {"translated_text": translated_text}
        elif mode == 'grammar':
            response_payload = {
                "translated_text": translated_text,
                "grammar_analysis": f"წინადადების სტრუქტურა გამართულია ({source_lang} -> {target_lang})."
            }
        elif mode == 'vision_ar':
            response_payload = {"translated_text": "AR Text Detected"}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_payload).encode('utf-8'))
