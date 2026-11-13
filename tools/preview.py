"""Temporary, read-only, loopback-only static preview. Python standard library only."""
import argparse
import json
import http.server
import pathlib
import socket
import threading
import time
import webbrowser

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOST, PORT = "127.0.0.1", 8777
ORIGIN = f"http://{HOST}:{PORT}"
PAGES = ("", "about", "services", "projects", "privacy-policy", "contact",
         "our-process", "bathroom-renovations", "kitchen-renovations",
         "basement-renovations", "flooring", "drywall-painting",
         "full-home-renovations", "garage-renovations")
FILES = ["assets/everstone-watermark.svg", "assets/style.css", "assets/main.js", "assets/favicon.svg", "assets/everstone-logo.png"]
FILES += [f"{page}/index.html" if page else "index.html" for page in PAGES]
for asset in json.loads((ROOT / "docs/asset-sources.json").read_text(encoding="utf-8")):
    relative = pathlib.PurePosixPath(asset["path"])
    if (relative.is_absolute() or ".." in relative.parts or
            relative.parts[:2] != ("assets", "local") or
            relative.suffix not in (".jpg", ".ttf", ".woff", ".woff2")):
        raise RuntimeError("Invalid asset publication path")
    FILES.append(relative.as_posix())
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf"}
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
       "font-src 'self'; connect-src 'none'; media-src 'none'; object-src 'none'; "
       "frame-src 'none'; worker-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
SNAPSHOT = {}
total = 0
for relative in FILES:
    path = ROOT / relative
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink() or ancestor.is_junction():
            raise RuntimeError("Linked files/directories are not allowed")
    if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
        raise RuntimeError("Missing or oversized preview file")
    data = path.read_bytes()
    total += len(data)
    if total > 25 * 1024 * 1024:
        raise RuntimeError("Preview snapshot exceeds 25 MiB")
    entry = (data, TYPES[path.suffix])
    SNAPSHOT["/" + relative] = entry
    if relative == "index.html":
        SNAPSHOT["/"] = entry
    elif relative.endswith("/index.html"):
        route = "/" + relative[:-10]
        SNAPSHOT[route] = SNAPSHOT[route.rstrip("/")] = entry

class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    server_version = ""
    sys_version = ""

    def setup(self):
        self.request.settimeout(2)
        super().setup()

    def log_message(self, format, *args):
        pass  # No request logging or filesystem-path disclosure.

    def send_response(self, code, message=None):
        self.send_response_only(code, message)  # No Server/Date fingerprint headers.

    def end_headers(self):
        for key, value in {
            "Connection": "close", "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer", "Content-Security-Policy": CSP,
            "Cross-Origin-Resource-Policy": "same-origin",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), serial=(), bluetooth=(), display-capture=()",
        }.items():
            self.send_header(key, value)
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        self.reply(code)

    def reply(self, code, data=b"", content_type="text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)
        self.close_connection = True

    def do_GET(self):
        # Exact numeric Host plus Origin/Fetch Metadata checks resist DNS rebinding
        # and browser cross-origin access. These do not authenticate local processes.
        if self.headers.get_all("Host") != [f"{HOST}:{PORT}"]:
            return self.reply(403)
        if any(len(self.headers.get_all(k, [])) > 1 for k in
               ("Origin", "Sec-Fetch-Site", "Content-Length", "Transfer-Encoding")):
            return self.reply(400)
        if self.headers.get("Origin", ORIGIN) != ORIGIN:
            return self.reply(403)
        if self.headers.get("Sec-Fetch-Site", "none") not in ("none", "same-origin"):
            return self.reply(403)
        if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Length", "0") != "0":
            return self.reply(400)
        # Exact in-memory lookup; no URL decoding or request-time disk access.
        entry = SNAPSHOT.get(self.path.split("?", 1)[0])
        if entry is None:
            return self.reply(404)
        return self.reply(200, *entry)

    do_HEAD = do_GET

class Server(http.server.HTTPServer):
    allow_reuse_address = False
    request_queue_size = 8

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def handle_error(self, request, client_address):
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open", action="store_true", help="Open the default browser")
    parser.add_argument("--port", type=int, default=8777, help="Loopback port (default: 8777)")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    PORT = args.port
    ORIGIN = f"http://{HOST}:{PORT}"
    with Server((HOST, PORT), Handler) as server:
        timer = threading.Timer(7200, server.shutdown)
        timer.daemon = True
        timer.start()
        print(f"Preview ready: {ORIGIN}/", flush=True)
        print("Snapshot loaded; photos/fonts are local; external requests blocked. Ctrl+C stops; expires in 2 hours.", flush=True)
        if args.open:
            webbrowser.open(ORIGIN + "/")
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
        finally:
            timer.cancel()
