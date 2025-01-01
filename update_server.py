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
    def __init__(self, *args, **kwargs):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.bootstrap_dir = os.path.join(self.base_dir, 'bootstrap')
        self.content_dir = os.path.join(self.base_dir, 'content')
        super().__init__(*args, **kwargs)

    def get_file_path(self, requested_path):
        """Determine the correct file path based on the request"""
        # Remove leading slash and normalize path
        clean_path = requested_path.lstrip('/')
        
        # Try bootstrap directory first
        if clean_path.startswith('bootstrap/'):
            file_path = os.path.join(self.base_dir, clean_path)
        # Then try content directory
        elif clean_path.startswith('content/'):
            file_path = os.path.join(self.base_dir, clean_path)
        # For root requests, try bootstrap directory
        else:
            file_path = os.path.join(self.bootstrap_dir, clean_path)
        
        return os.path.normpath(file_path)

    def do_GET(self):
        """Handle GET requests"""
        try:
            file_path = self.get_file_path(self.path)
            logging.info(f"Checking for file: {file_path}")
            
            # Prevent directory traversal
            if not (os.path.abspath(file_path).startswith(os.path.abspath(self.bootstrap_dir)) or 
                   os.path.abspath(file_path).startswith(os.path.abspath(self.content_dir))):
                self.send_error(403, "Forbidden")
                logging.warning(f"Attempted directory traversal: {file_path}")
                return

            # Check if file exists
            if not os.path.exists(file_path):
                self.send_error(404, f"File not found: {self.path}")
                return

            # Get file size and modification time
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            last_modified = datetime.fromtimestamp(file_stats.st_mtime).strftime('%a, %d %b %Y %H:%M:%S GMT')

            # Determine content type
            content_type = 'application/octet-stream'
            if file_path.endswith('.txt'):
                content_type = 'text/plain'
            elif file_path.endswith('.xml'):
                content_type = 'application/xml'
            elif file_path.endswith('.xz'):
                content_type = 'application/x-xz'
            elif file_path.endswith('.exe'):
                content_type = 'application/x-msdownload'

            # Send headers
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', file_size)
            self.send_header('Last-Modified', last_modified)
            self.end_headers()

            # Log the request
            logging.info(f"Serving {self.path} ({file_size} bytes)")

            # Send file content
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())

        except Exception as e:
            logging.error(f"Error serving {self.path}: {str(e)}")
            self.send_error(500, f"Internal server error: {str(e)}")

    def log_message(self, format, *args):
        """Override to use our logging configuration"""
        logging.info(format % args)

def list_directory_files(base_dir, directory, prefix=''):
    """Recursively list all files in a directory with their sizes"""
    files = []
    try:
        for root, dirs, filenames in os.walk(directory):
            rel_path = os.path.relpath(root, base_dir)
            if rel_path == '.':
                current_prefix = prefix
            else:
                current_prefix = f"{prefix}{rel_path}/"
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                size = os.path.getsize(file_path)
                files.append(f" - {current_prefix}{filename} ({size:,} bytes)")
    except Exception as e:
        logging.error(f"Error listing directory {directory}: {str(e)}")
    return sorted(files)  # Sort files for consistent output

def run_server(host='0.0.0.0', port=80):
    """Run the update server"""
    try:
        server = HTTPServer((host, port), UpdateServer)
        print(f"Starting update server on {host}:{port}")
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # List bootstrap files
        bootstrap_path = os.path.join(base_dir, 'bootstrap')
        print(f"\nServing bootstrap files from {bootstrap_path}:")
        for file_info in list_directory_files(base_dir, bootstrap_path, 'bootstrap/'):
            print(file_info)
            
        # List content files
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
