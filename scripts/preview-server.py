#!/usr/bin/env python3
"""Local preview server with caching disabled.

Python's stock http.server lets browsers reuse a stale HTML document after a
rebuild. These headers force revalidation on every request.
"""
from __future__ import annotations

import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main() -> None:
    port = int(os.environ.get("WIKI_PREVIEW_PORT", "8765"))
    server = ThreadingHTTPServer(("", port), NoCacheHandler)
    print(f"Wiki preview: http://localhost:{port} (cache disabled)")
    server.serve_forever()


if __name__ == "__main__":
    main()
