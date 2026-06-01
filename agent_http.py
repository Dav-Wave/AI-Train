"""
agent_http.py — HTTP wrapper for the brief generator
------------------------------------------------------
Exposes agent.py as a simple HTTP server so n8n can call it.
Run this alongside your n8n workflow in Session 4.

Usage:
    python agent_http.py
    # Server runs on http://localhost:8080
    # n8n HTTP Request node points to: http://localhost:8080/brief

For production deployment to Render/Railway:
    - Set ANTHROPIC_API_KEY as an environment variable in the platform
    - Use the platform-provided URL in n8n instead of localhost
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from agent import generate_brief


class BriefHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/brief":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            
            raw_input = body.get("raw_input", "")
            context = body.get("context", "")
            
            if not raw_input:
                self._respond(400, {"error": "raw_input is required"})
                return
            
            try:
                result = generate_brief(raw_input, context=context)
                self._respond(200, result)
            except Exception as e:
                self._respond(500, {"error": str(e)})
        
        elif self.path == "/health":
            self._respond(200, {"status": "ok"})
        
        else:
            self._respond(404, {"error": "Not found"})
    
    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok"})
        else:
            self._respond(404, {"error": "Not found"})
    
    def _respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), BriefHandler)
    print(f"Brief Generator HTTP server running on port {port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"Generate brief: POST http://localhost:{port}/brief")
    print('  Body: {"raw_input": "your feedback text"}')
    server.serve_forever()
