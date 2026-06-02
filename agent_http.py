"""
agent_http.py — HTTP wrapper for n8n (Session 4)
-------------------------------------------------
Exposes agent.py as a simple HTTP server so n8n Cloud can call it.

Usage:
    python3 agent_http.py             # runs on :8080
    PORT=9000 python3 agent_http.py   # custom port

Expose publicly for n8n Cloud:
    npx ngrok http 8080
    # Use the https://xxx.ngrok.app URL in n8n HTTP Request node
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
            context   = body.get("context", "")
            if not raw_input:
                self._respond(400, {"error": "raw_input is required"})
                return
            try:
                result = generate_brief(raw_input, context=context)
                self._respond(200, result)
            except Exception as e:
                self._respond(500, {"error": str(e)})
        else:
            self._respond(404, {"error": "Not found"})

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok", "model": "llama-3.3-70b-versatile (Groq)"})
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
    print(f"✓ Brief Generator running on port {port}  (Groq / Llama 3.3 70B — FREE)")
    print(f"  Health:   GET  http://localhost:{port}/health")
    print(f"  Generate: POST http://localhost:{port}/brief")
    print(f'  Body: {{"raw_input": "your feedback text"}}')
    server.serve_forever()
