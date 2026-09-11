from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        if self.path == '/translate-text':
            params = urllib.parse.parse_qs(body.decode('utf-8'))
            text = params.get('text', [''])[0]
            src_lang = params.get('src_lang', ['en'])[0]
            target_lang = params.get('target_lang', ['ka'])[0]

            # Google Translate Unofficial API call
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_lang}&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    translated_text = "".join([item[0] for item in res_data[0] if item[0]])
                
                self._send_json({"translated_text": translated_text})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        elif self.path == '/ocr-translate':
            self._send_json({"extracted_text": "", "translated_text": "OCR API endpoint is active"})
        else:
            self._send_json({"error": "Not Found"}, status=404)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
