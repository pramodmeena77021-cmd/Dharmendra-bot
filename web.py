import os
import http.server

port = int(os.environ.get("PORT", 8000))
server = http.server.HTTPServer(("", port), http.server.SimpleHTTPRequestHandler)
print(f"Server running on port {port}")
server.serve_forever()
