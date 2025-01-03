from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_server.log'),
        logging.StreamHandler()
    ]
)

class UpdateServer(BaseHTTPRequestHandler):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BOOTSTRAP_DIR = os.path.join(BASE_DIR, 'bootstrap')
    CONTENT_DIR = os.path.join(BASE_DIR, 'content')
    CONTENT_TYPES = {
        '.txt': 'text/plain',
        '.xml': 'application/xml',
        '.xz': 'application/x-xz',
        '.exe': 'application/x-msdownload'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_file_path(self, requested_path):
        """Determine the correct file path based on the request."""
        clean_path = requested_path.lstrip('/')
        if clean_path.startswith('bootstrap/'):
            return os.path.join(self.BASE_DIR, clean_path)
        elif clean_path.startswith('content/'):
            return os.path.join(self.BASE_DIR, clean_path)
        return os.path.join(self.BOOTSTRAP_DIR, clean_path)

    def is_valid_path(self, file_path):
        """Check if the file path is within allowed directories."""
        abs_path = os.path.abspath(file_path)
        return abs_path.startswith(os.path.abspath(self.BOOTSTRAP_DIR)) or \
               abs_path.startswith(os.path.abspath(self.CONTENT_DIR))

    def get_content_type(self, file_path):
        """Determine the content type based on the file extension."""
        _, ext = os.path.splitext(file_path)
        return self.CONTENT_TYPES.get(ext, 'application/octet-stream')

    def do_GET(self):
        """Handle GET requests."""
        try:
            file_path = self.get_file_path(self.path)
            logging.info(f"Checking for file: {file_path}")

            if not self.is_valid_path(file_path):
                self.send_error(403, "Forbidden")
                logging.warning(f"Attempted directory traversal: {file_path}")
                return

            if not os.path.exists(file_path):
                self.send_error(404, f"File not found: {self.path}")
                return

            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            last_modified = datetime.fromtimestamp(file_stats.st_mtime).strftime('%a, %d %b %Y %H:%M:%S GMT')
            content_type = self.get_content_type(file_path)

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', file_size)
            self.send_header('Last-Modified', last_modified)
            self.end_headers()

            logging.info(f"Serving {self.path} ({file_size} bytes)")

            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())

        except Exception as e:
            logging.error(f"Error serving {self.path}: {str(e)}")
            self.send_error(500, f"Internal server error: {str(e)}")

    def log_message(self, format, *args):
        """Override to use our logging configuration."""
        logging.info(format % args)

def list_directory_files(base_dir, directory, prefix=''):
    """Recursively list all files in a directory with their sizes."""
    files = []
    try:
        for root, _, filenames in os.walk(directory):
            rel_path = os.path.relpath(root, base_dir)
            current_prefix = f"{prefix}{rel_path}/" if rel_path != '.' else prefix
            for filename in filenames:
                file_path = os.path.join(root, filename)
                size = os.path.getsize(file_path)
                files.append(f" - {current_prefix}{filename} ({size:,} bytes)")
    except Exception as e:
        logging.error(f"Error listing directory {directory}: {str(e)}")
    return sorted(files)

def run_server(host='0.0.0.0', port=80):
    """Run the update server."""
    try:
        server = HTTPServer((host, port), UpdateServer)
        print(f"Starting update server on {host}:{port}")

        base_dir = os.path.dirname(os.path.abspath(__file__))

        bootstrap_path = os.path.join(base_dir, 'bootstrap')
        print(f"\nServing bootstrap files from {bootstrap_path}:")
        for file_info in list_directory_files(base_dir, bootstrap_path, 'bootstrap/'):
            print(file_info)

        content_path = os.path.join(base_dir, 'content')
        print(f"\nServing content files from {content_path}:")
        for file_info in list_directory_files(base_dir, content_path, 'content/'):
            print(file_info)

        print("\nServer is ready to handle requests...")
        server.serve_forever()
    except Exception as e:
        logging.error(f"Server error: {str(e)}")
        if "Permission denied" in str(e):
            print("\nError: Permission denied. Try running with administrator privileges.")
            print("The server needs to run on port 80 to handle game client requests.")

if __name__ == "__main__":
    run_server()