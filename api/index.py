import json
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler


def translate_text(text, src, target):
  params = {
      'client': 'gtx',
      'sl': src,
      'tl': target,
      'dt': 't',
      'q': text,
  }
  url = 'https://translate.googleapis.com/translate_a/single?' + urllib.parse.urlencode(
      params
  )

  req = urllib.request.Request(
      url,
      headers={
          'User-Agent': (
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
              ' (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
          )
      },
  )

  try:
    with urllib.request.urlopen(req, timeout=10) as response:
      res_body = response.read().decode('utf-8')
      data = json.loads(res_body)
      translated_parts = [item[0] for item in data[0] if item and item[0]]
      return ''.join(translated_parts)
  except Exception as e:
    raise Exception(f'Google Translation Error: {str(e)}')


class handler(BaseHTTPRequestHandler):

  def do_OPTIONS(self):
    self.send_response(200)
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    self.send_header(
        'Access-Control-Allow-Headers', 'Content-Type, Authorization'
    )
    self.end_headers()

  def do_GET(self):
    # მხარდაჭერა GET მოთხოვნებისთვისაც (ტესტირებისთვის)
    parsed_path = urllib.parse.urlparse(self.path)
    query = urllib.parse.parse_qs(parsed_path.query)

    text = query.get('text', [''])[0]
    source = query.get('source', ['auto'])[0]
    target = query.get('target', ['en'])[0]

    if not text:
      self.send_response(400)
      self.send_header('Content-Type', 'application/json; charset=utf-8')
      self.send_header('Access-Control-Allow-Origin', '*')
      self.end_headers()
      self.wfile.write(
          json.dumps({'error': 'No text provided'}).encode('utf-8')
      )
      return

    try:
      result = translate_text(text, source, target)
      self.send_response(200)
      self.send_header('Content-Type', 'application/json; charset=utf-8')
      self.send_header('Access-Control-Allow-Origin', '*')
      self.end_headers()
      self.wfile.write(
          json.dumps({'translated_text': result}, ensure_ascii=False).encode(
              'utf-8'
          )
      )
    except Exception as e:
      self.send_response(500)
      self.send_header('Content-Type', 'application/json; charset=utf-8')
      self.send_header('Access-Control-Allow-Origin', '*')
      self.end_headers()
      self.wfile.write(
          json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8')
      )

  def do_POST(self):
    try:
      content_length = int(self.headers.get('Content-Length', 0))
      if content_length > 0:
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_data)
      else:
        data = {}

      text = data.get('text', '')
      source = data.get('source', 'auto')
      target = data.get('target', 'en')

      if not text:
        self.send_response(400)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(
            json.dumps({'error': 'Empty text input'}).encode('utf-8')
        )
        return

      result = translate_text(text, source, target)

      self.send_response(200)
      self.send_header('Content-Type', 'application/json; charset=utf-8')
      self.send_header('Access-Control-Allow-Origin', '*')
      self.end_headers()
      self.wfile.write(
          json.dumps({'translated_text': result}, ensure_ascii=False).encode(
              'utf-8'
          )
      )

    except Exception as e:
      self.send_response(500)
      self.send_header('Content-Type', 'application/json; charset=utf-8')
      self.send_header('Access-Control-Allow-Origin', '*')
      self.end_headers()
      self.wfile.write(
          json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8')
      )
