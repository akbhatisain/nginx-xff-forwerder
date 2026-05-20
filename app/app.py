from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = {
            "remote_addr": self.client_address[0],
            "method": self.command,
            "path": self.path,
            "headers": {k: v for k, v in self.headers.items()},
            "x_forwarded_for": self.headers.get("X-Forwarded-For", ""),
            "x_real_ip": self.headers.get("X-Real-IP", ""),
            "via_node": self.headers.get("X-Proxy-Node", ""),
        }
        body = json.dumps(data, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()