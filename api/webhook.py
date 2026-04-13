import asyncio
import base64
import io
import json
import os
from http.server import BaseHTTPRequestHandler

import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY", "")
IMGBB_URL = "https://api.imgbb.com/1/upload"
LITTERBOX_URL = "https://litterbox.catbox.moe/resources/internals/api.php"


async def upload_image(image_bytes: bytes, filename: str, mime: str) -> dict:
    if IMGBB_API_KEY:
        b64 = base64.b64encode(image_bytes).decode()
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                IMGBB_URL,
                params={"key": IMGBB_API_KEY},
                data={"image": b64, "name": filename},
            )
            if r.status_code == 200:
                data = r.json().get("data", {})
                return {
                    "url": data.get("url", ""),
                    "service": "ImgBB",
                }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            LITTERBOX_URL,
            data={"reqtype": "fileupload", "time": "72h"},
            files={"fileToUpload": (filename, image_bytes, mime)},
        )
        r.raise_for_status()
        url = r.text.strip()
        if url.startswith("https://"):
            return {"url": url, "service": "Litterbox"}
        raise ValueError(f"Unexpected response: {url}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service_info = (
        "🔑 <b>ImgBB</b> (link ជារៀងរហូត)"
        if IMGBB_API_KEY
        else "📦 <b>Litterbox</b> (link រយៈពេល 72 ម៉ោង)\n\n"
        "💡 <i>ចង់បាន permanent link? Set <code>IMGBB_API_KEY</code> ក្នុង Secrets!</i>"
    )
    text = (
        "👋 សួស្តី! ខ្ញុំជា <b>Image Link Bot</b>\n\n"
        "📤 ផ្ញើរូបភាពមកខ្ញុំ ខ្ញុំនឹង upload ហើយបញ្ជូន link "
        "ដែលបង្ហាញ <b>preview</b> នៅក្នុង Telegram!\n\n"
        f"🗄 <b>Service:</b> {service_info}\n\n"
        "📸 <i>ចុះផ្ញើរូបភាពសាកល្បងមើល...</i>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def send_result(update: Update, result: dict):
    await update.message.reply_text(result["url"], do_quote=True)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ កំពុង upload រូបភាព...", do_quote=True)
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = bytes(await file.download_as_bytearray())
    try:
        result = await upload_image(file_bytes, "photo.jpg", "image/jpeg")
        await msg.delete()
        await send_result(update, result)
    except Exception as e:
        await msg.edit_text(f"❌ Upload បរាជ័យ: {str(e)}\nសូមព្យាយាមម្តងទៀត។")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    mime = doc.mime_type or ""
    if not mime.startswith("image/"):
        await update.message.reply_text(
            "⚠️ ខ្ញុំអាចដំណើរការបានតែ <b>រូបភាព</b>ប៉ុណ្ណោះ។\nសូមផ្ញើ Photo ឬ Image file។",
            parse_mode="HTML",
        )
        return
    msg = await update.message.reply_text("⏳ កំពុង upload រូបភាព...", do_quote=True)
    file = await context.bot.get_file(doc.file_id)
    file_bytes = bytes(await file.download_as_bytearray())
    ext = mime.split("/")[-1]
    try:
        result = await upload_image(file_bytes, f"image.{ext}", mime)
        await msg.delete()
        await send_result(update, result)
    except Exception as e:
        await msg.edit_text(f"❌ Upload បរាជ័យ: {str(e)}\nសូមព្យាយាមម្តងទៀត។")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 សូមផ្ញើ <b>រូបភាព</b>មកខ្ញុំ!",
        parse_mode="HTML",
    )


def build_app():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
    application.add_handler(MessageHandler(filters.ALL, unknown))
    return application


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
