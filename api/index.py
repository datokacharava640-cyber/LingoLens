from http.server import BaseHTTPRequestHandler
import json
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_data = {
            "status": "online",
            "message": "LingoLens API is running successfully!"
        }
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_data = {
            "status": "success",
            "message": "Request processed successfully"
        }
        self.wfile.write(json.dumps(response_data).encode('utf-8'))
