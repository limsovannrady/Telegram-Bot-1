import asyncio
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from bot import build_app

_app = None


async def get_app():
    global _app
    if _app is None:
        _app = build_app()
        await _app.initialize()
    return _app


async def process_update(body: bytes):
    application = await get_app()
    update = Update.de_json(json.loads(body), application.bot)
    await application.process_update(update)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        asyncio.run(process_update(body))

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, format, *args):
        pass
