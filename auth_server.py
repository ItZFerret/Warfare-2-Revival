import http.server
import time
import json
import sys
import html
import urllib.parse

class AuthServer(http.server.BaseHTTPRequestHandler):
    def log_request_details(self):
        sys.stdout.flush()
        print("\n=== Incoming Auth Request ===")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Client Address: {self.client_address}")
        print(f"Request Method: {self.command}")
        print(f"Path: {self.path}")
        print(f"Host: {self.headers.get('Host', '')}")
        print("\nHeaders:")
        for header, value in self.headers.items():
            print(f"{header}: {value}")
        sys.stdout.flush()

    def clean_input(self, text):
        """Clean input like PHP's htmlspecialchars and newline handling"""
        # Replace newlines like PHP
        text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\0', '')
        # Escape special chars like PHP's htmlspecialchars
        text = html.escape(text, quote=True)
        return text.strip()

    def do_GET(self):
        self.log_request_details()
        print(f"\nUnexpected GET request to auth server: {self.path}\n")
        sys.stdout.flush()
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        # Log basic request info first
        self.log_request_details()
        
        # Check if this is an auth request
        if not self.path.endswith('/remauth.php'):
            print(f"\nUnknown POST request: {self.path}")
            sys.stdout.flush()
            self.send_response(404)
            self.end_headers()
            return
            
        try:
            # Read and log POST data
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            print("\nPOST Data:")
            print(f"Raw bytes: {body}")
            raw_data = body.decode('utf-8', errors='ignore')
            print(f"Raw string: {raw_data}")
            print(f"Hex: {body.hex()}")
            
            # Try to parse as form data
            try:
                form_data = urllib.parse.parse_qs(raw_data)
                print(f"Form data: {form_data}")
            except:
                print("Failed to parse as form data")
            
            print(f"Raw decoded: {raw_data}")
            sys.stdout.flush()
            
            print("\n=== Processing Auth Request ===")
            
            # Convert && to space then parse with two spaces like PHP
            parsed = raw_data.replace('&&', '  ')
            print(f"After && replacement: {parsed}")
            
            # Split on two spaces like sscanf
            parts = parsed.split('  ', 1)  # Split on first occurrence of two spaces
            print(f"Split parts: {parts}")
            
            username = parts[0] if len(parts) > 0 else ''
            password = parts[1] if len(parts) > 1 else ''
            
            print(f"Username: {username}")
            print(f"Password: {password}")
            
            # For testing, accept any non-empty login
            # In production this would check against MySQL with SHA1 password
            if username and password:
                print("\n=== Login Success ===")
                status = 'ok'
                message = 'Success.'
                user_id = '12345'  # Would come from MySQL
                email = f"{username}@example.com"  # Would come from MySQL
                session_id = f"{int(time.time()):x}"  # Simple hex timestamp for testing
            else:
                print("\n=== Login Failed ===")
                status = 'fail'
                message = 'Username and/or password is empty.'
                user_id = '1'
                username = 'Anonymous'
                email = 'anonymous@example.com'
                session_id = '0'
            
            # Build response string exactly like DWAuth class
            response = f"{status}#{message}#{user_id}#{username}#{email}#{session_id}#"
            response_bytes = response.encode('utf-8')
            
            print("\n=== Sending Response ===")
            print(f"Response string: {response}")
            print(f"Response bytes: {response_bytes}")
            
            # Send headers
            print("\n=== Sending Headers ===")
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(response_bytes)))
            self.send_header('Connection', 'keep-alive')
            self.send_header('Keep-Alive', 'timeout=300, max=1000')
            self.end_headers()
            
            # Send response body
            print("\n=== Sending Body ===")
            self.wfile.write(response_bytes)
            self.wfile.flush()
            
            print("=== Response Complete ===\n")
            sys.stdout.flush()
            
        except Exception as e:
            print("\n=== Error Processing Request ===")
            print(f"Error type: {type(e)}")
            print(f"Error message: {str(e)}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            sys.stdout.flush()
            
            # Send error response
            try:
                error_response = "fail#Server error#1#Anonymous#anonymous@example.com#0#"
                error_bytes = error_response.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Length', str(len(error_bytes)))
                self.end_headers()
                self.wfile.write(error_bytes)
                self.wfile.flush()
            except:
                print("Failed to send error response")
                sys.stdout.flush()

def run_server(port=1337):
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, AuthServer)
    httpd.protocol_version = 'HTTP/1.1'
    
    print(f"\nStarting Auth Server on port {port}")
    print(f"Handling domain: auth.iw4.prod.fourdeltaone.net")
    print(f"Protocol: HTTP/1.1 with keep-alive")
    print(f"Endpoints:")
    print(f"- Authentication (/remauth.php)")
    print(f"Waiting for requests...")
    sys.stdout.flush()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.stdout.flush()
        httpd.server_close()

if __name__ == '__main__':
    run_server(1337)
