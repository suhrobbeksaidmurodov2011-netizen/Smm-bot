import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
import database as db
from handlers_user import register_user_handlers
from handlers_admin import register_admin_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot ishlayapti")

    def log_message(self, format, *args):
        pass  # health-check so'rovlarini logga chiqarmaslik


def _run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    server.serve_forever()


def main():
    # Render Web Service portga ulanishini kutadi - shu uchun
    # alohida oqimda (thread) oddiy HTTP server ishga tushiramiz.
    threading.Thread(target=_run_health_server, daemon=True).start()

    db.init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    register_user_handlers(app)
    register_admin_handlers(app)

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
