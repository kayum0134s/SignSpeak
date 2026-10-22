"""
SignSpeak - Local Development Server
Simple HTTP server to run the sign language application
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Configuration
PORT = 8000
HOST = "localhost"

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve files with correct MIME types"""
    
    def end_headers(self):
        # Enable CORS for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Serve index.html for root path
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

def main():
    # Resolve frontend directory
    project_root = Path(__file__).resolve().parent.parent
    frontend_dir = project_root / "frontend"
    os.chdir(frontend_dir)
    
    # Create server
    handler = MyHttpRequestHandler
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://{HOST}:{PORT}"
        
        print("=" * 60)
        print("🤟 SignSpeak Server Started!")
        print("=" * 60)
        print(f"Server running at: {url}")
        print(f"Directory: {frontend_dir}")
        print("\nPress Ctrl+C to stop the server")
        print("=" * 60)
        
        # Open browser automatically
        try:
            webbrowser.open(url)
            print(f"✅ Opening browser at {url}")
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print(f"   Please open {url} manually")
        
        print("\n🎬 Ready! Translate text to sign language videos.")
        print("=" * 60)
        
        # Start server
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped. Goodbye!")

if __name__ == "__main__":
    main()
