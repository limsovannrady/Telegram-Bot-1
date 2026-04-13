import os
import io
import base64
import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY", "")

IMGBB_URL = "https://api.imgbb.com/1/upload"
LITTERBOX_URL = "https://litterbox.catbox.moe/resources/internals/api.php"


async def upload_image(image_bytes: bytes, filename: str, mime: str) -> dict:
    """Upload image and return dict with url, delete_url, expiry info."""

    # Try imgbb if API key is set (permanent links)
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
                    "display_url": data.get("display_url", data.get("url", "")),
                    "delete_url": data.get("delete_url", ""),
                    "service": "ImgBB",
                    "expiry": "ជារៀងរហូត (permanent)",
                }

    # Fallback: litterbox (72 hours)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            LITTERBOX_URL,
            data={"reqtype": "fileupload", "time": "72h"},
            files={"fileToUpload": (filename, image_bytes, mime)},
        )
        r.raise_for_status()
        url = r.text.strip()
        if url.startswith("https://"):
            return {
                "url": url,
                "display_url": url,
                "delete_url": "",
                "service": "Litterbox",
                "expiry": "72 ម៉ោង (បន្ទាប់មក link នឹងផុតកំណត់)",
            }
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



async def send_result(update: Update, result: dict, file_id: str, is_photo: bool):
    url = result["url"]
    await update.message.reply_text(url, do_quote=True)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ កំពុង upload រូបភាព...", do_quote=True)

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = bytes(await file.download_as_bytearray())

    try:
        result = await upload_image(file_bytes, "photo.jpg", "image/jpeg")
        await msg.delete()
        await send_result(update, result, photo.file_id, is_photo=True)
    except Exception as e:
        await msg.edit_text(f"❌ Upload បរាជ័យ: {str(e)}\nសូមព្យាយាមម្តងទៀត។")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    mime = doc.mime_type or ""

    if not mime.startswith("image/"):
        await update.message.reply_text(
            "⚠️ ខ្ញុំអាចដំណើរការបានតែ <b>រូបភាព</b>ប៉ុណ្ណោះ។\n"
            "សូមផ្ញើ Photo ឬ Image file។",
            parse_mode="HTML",
        )
        return

    msg = await update.message.reply_text("⏳ កំពុង upload រូបភាព...", do_quote=True)

    file = await context.bot.get_file(doc.file_id)
    file_bytes = bytes(await file.download_as_bytearray())

    ext = mime.split("/")[-1]
    filename = f"image.{ext}"

    try:
        result = await upload_image(file_bytes, filename, mime)
        await msg.delete()
        await send_result(update, result, doc.file_id, is_photo=False)
    except Exception as e:
        await msg.edit_text(f"❌ Upload បរាជ័យ: {str(e)}\nសូមព្យាយាមម្តងទៀត។")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 សូមផ្ញើ <b>រូបភាព</b>មកខ្ញុំ!",
        parse_mode="HTML",
    )


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
app.add_handler(MessageHandler(filters.ALL, unknown))
app.run_polling()
