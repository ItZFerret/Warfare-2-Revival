import http.server
import time
import sys
import html
import urllib.parse
import traceback


class AuthServer(http.server.BaseHTTPRequestHandler):
    def log_request_details(self):
        """Log details of the incoming request."""
        sys.stdout.flush()
        print(f"\n=== Incoming Auth Request ===\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
              f"Client Address: {self.client_address}\nRequest Method: {self.command}\nPath: {self.path}\n"
              f"Host: {self.headers.get('Host', '')}\nHeaders:")
        for header, value in self.headers.items():
            print(f"{header}: {value}")
        sys.stdout.flush()

    @staticmethod
    def clean_input(text):
        """Clean input like PHP's htmlspecialchars and newline handling."""
        return html.escape(text.replace('\r\n', '\n').replace('\r', '\n').replace('\0', ''), quote=True).strip()

    def handle_auth_request(self, raw_data):
        """Process the authentication request."""
        parts = raw_data.replace('&&', '  ').split('  ', 1)
        username, password = (parts + [''])[:2]
        if username and password:
            return {"status": "ok", "message": "Success.", "user_id": "12345", "username": username,
                    "email": f"{username}@example.com", "session_id": f"{int(time.time()):x}"}
        return {"status": "fail", "message": "Username and/or password is empty.", "user_id": "1",
                "username": "Anonymous", "email": "anonymous@example.com", "session_id": "0"}

    def send_response_data(self, response_data):
        """Send the response back to the client."""
        response = f"{response_data['status']}#{response_data['message']}#{response_data['user_id']}#" \
                   f"{response_data['username']}#{response_data['email']}#{response_data['session_id']}#"
        response_bytes = response.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.send_header('Connection', 'keep-alive')
        self.send_header('Keep-Alive', 'timeout=300, max=1000')
        self.end_headers()
        self.wfile.write(response_bytes)
        self.wfile.flush()

    def do_GET(self):
        """Handle GET requests."""
        self.log_request_details()
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        """Handle POST requests."""
        self.log_request_details()
        if not self.path.endswith('/remauth.php'):
            self.send_response(404)
            self.end_headers()
            return
        try:
            raw_data = self.rfile.read(int(self.headers.get('Content-Length', 0))).decode('utf-8', errors='ignore')
            response_data = self.handle_auth_request(raw_data)
            self.send_response_data(response_data)
        except Exception as e:
            print(f"\n=== Error Processing Request ===\nError: {e}\nTraceback:\n{traceback.format_exc()}")
            sys.stdout.flush()
            self.send_response_data({"status": "fail", "message": "Server error", "user_id": "1",
                                     "username": "Anonymous", "email": "anonymous@example.com", "session_id": "0"})


def run_server(port=1337):
    """Run the authentication server."""
    print(f"\nStarting Auth Server on port {port}\nHandling domain: auth.iw4.prod.fourdeltaone.net\n"
          f"Protocol: HTTP/1.1 with keep-alive\nEndpoints:\n- Authentication (/remauth.php)\nWaiting for requests...")
    sys.stdout.flush()
    http.server.HTTPServer(('', port), AuthServer).serve_forever()


if __name__ == '__main__':
    try:
        run_server(1337)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.stdout.flush()
