import json
from http.server import BaseHTTPRequestHandler
import urllib.parse
import urllib.request


def fetch_translation(text, source_lang, target_lang):
  params = {
      'client': 'gtx',
      'sl': source_lang,
      'tl': target_lang,
      'dt': 't',
      'q': text,
  }
  url = (
      'https://translate.googleapis.com/translate_a/single?'
      + urllib.parse.urlencode(params)
  )

  req = urllib.request.Request(
      url,
      headers={
          'User-Agent': (
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          )
      },
  )

  with urllib.request.urlopen(req, timeout=8) as response:
    if response.status == 200:
      res_body = response.read().decode('utf-8')
      data = json.loads(res_body)
      translated_parts = [item[0] for item in data[0] if item and item[0]]
      return ''.join(translated_parts)
    else:
      raise Exception(f'Google API Error: {response.status}')


class handler(BaseHTTPRequestHandler):

  def do_OPTIONS(self):
    self.send_response(200)
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    self.end_headers()

  def do_POST(self):
    try:
      content_length = int(self.headers.get('Content-Length', 0))
      body = self.rfile.read(content_length).decode('utf-8')
      data = json.loads(body) if body else {}

      text = data.get('text', '')
      source = data.get('source', 'auto')
      target = data.get('target', 'en')

      if not text:
        self.send_response(400)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'error': 'Empty text'}).encode('utf-8'))
        return

      translated_text = fetch_translation(text, source, target)

      self.send_response(200)
      self.send_header('Content-Type', 'application/json; charset=utf-8')
      self.send_header('Access-Control-Allow-Origin', '*')
      self.end_headers()
      response_data = json.dumps(
          {'translated_text': translated_text}, ensure_ascii=False
      )
      self.wfile.write(response_data.encode('utf-8'))

    except Exception as e:
      self.send_response(500)
      self.send_header('Content-Type', 'application/json; charset=utf-8')
      self.send_header('Access-Control-Allow-Origin', '*')
      self.end_headers()
      error_data = json.dumps({'error': str(e)}, ensure_ascii=False)
      self.wfile.write(error_data.encode('utf-8'))
