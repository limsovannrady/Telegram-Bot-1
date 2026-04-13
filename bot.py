import os
import io
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

TELEGRAPH_UPLOAD_URL = "https://telegra.ph/upload"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 សួស្តី! ខ្ញុំជា <b>Image Link Bot</b>\n\n"
        "📤 ផ្ញើរូបភាពមកខ្ញុំ រួចខ្ញុំនឹងបង្ហូររូបភាពនោះ "
        "ឡើងទៅ <b>Telegraph</b> ហើយបញ្ជូន link មកវិញ។\n\n"
        "🔗 Link នោះអាចបង្ហាញ <b>preview</b> បាននៅក្នុង Telegram!\n\n"
        "📸 <i>ចុះផ្ញើរូបភាពសាកល្បងមើល...</i>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 <b>របៀបប្រើប្រាស់</b>\n\n"
        "1️⃣ ផ្ញើរូបភាព (Photo) ណាមួយមកខ្ញុំ\n"
        "2️⃣ ខ្ញុំនឹង upload ឡើង Telegraph\n"
        "3️⃣ ខ្ញុំផ្ញើ link មកវិញ\n"
        "4️⃣ Copy link ហើយចែករំលែកបាន!\n\n"
        "✅ Link ដែលបានមក អាចបង្ហាញ preview "
        "ពេល paste នៅក្នុង Telegram chat.\n\n"
        "⚠️ <b>ចំណាំ:</b> ផ្ញើជា Photo (មិនមែន File) ដើម្បីឱ្យល្អបំផុត។"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ កំពុង upload រូបភាព...")

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    file_bytes = await file.download_as_bytearray()

    file_obj = io.BytesIO(bytes(file_bytes))
    file_obj.name = "image.jpg"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                TELEGRAPH_UPLOAD_URL,
                files={"file": ("image.jpg", file_obj, "image/jpeg")},
            )
            response.raise_for_status()
            data = response.json()

        if isinstance(data, list) and len(data) > 0 and "src" in data[0]:
            src = data[0]["src"]
            image_url = f"https://telegra.ph{src}"

            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔗 បើក Link", url=image_url)]]
            )

            caption = (
                f"✅ <b>Upload រួចរាល់!</b>\n\n"
                f"🔗 <b>Link:</b>\n"
                f"<code>{image_url}</code>\n\n"
                f"📋 Copy link ខាងលើ ហើយ paste "
                f"នៅក្នុង chat ណាក៏បាន — Telegram នឹងបង្ហាញ preview ដោយស្វ័យប្រវត្តិ!"
            )

            await update.message.reply_photo(
                photo=photo.file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_text(
                "❌ Upload បរាជ័យ។ សូមព្យាយាមម្តងទៀត។"
            )

    except httpx.HTTPStatusError as e:
        await update.message.reply_text(
            f"❌ Server error: {e.response.status_code}\nសូមព្យាយាមម្តងទៀត។"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ មានបញ្ហាកើតឡើង: {str(e)}\nសូមព្យាយាមម្តងទៀត។"
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    mime = doc.mime_type or ""

    if not mime.startswith("image/"):
        await update.message.reply_text(
            "⚠️ ខ្ញុំអាចដំណើរការបានតែរូបភាពប៉ុណ្ណោះ។\n"
            "សូមផ្ញើ <b>Photo</b> (មិនមែន File)។",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text("⏳ កំពុង upload រូបភាព (as file)...")

    file = await context.bot.get_file(doc.file_id)
    file_bytes = await file.download_as_bytearray()

    ext = mime.split("/")[-1]
    filename = f"image.{ext}"
    file_obj = io.BytesIO(bytes(file_bytes))
    file_obj.name = filename

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                TELEGRAPH_UPLOAD_URL,
                files={"file": (filename, file_obj, mime)},
            )
            response.raise_for_status()
            data = response.json()

        if isinstance(data, list) and len(data) > 0 and "src" in data[0]:
            src = data[0]["src"]
            image_url = f"https://telegra.ph{src}"

            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔗 បើក Link", url=image_url)]]
            )

            caption = (
                f"✅ <b>Upload រួចរាល់!</b>\n\n"
                f"🔗 <b>Link:</b>\n"
                f"<code>{image_url}</code>\n\n"
                f"📋 Copy link ខាងលើ ហើយ paste "
                f"នៅក្នុង chat ណាក៏បាន — Telegram នឹងបង្ហាញ preview ដោយស្វ័យប្រវត្តិ!"
            )

            await update.message.reply_document(
                document=doc.file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_text(
                "❌ Upload បរាជ័យ។ សូមព្យាយាមម្តងទៀត។"
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ មានបញ្ហាកើតឡើង: {str(e)}\nសូមព្យាយាមម្តងទៀត។"
        )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 សូមផ្ញើ<b>រូបភាព</b>មកខ្ញុំ!\n"
        "ឬប្រើ /help ដើម្បីមើលការណែនាំ។",
        parse_mode="HTML",
    )


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
app.add_handler(MessageHandler(filters.ALL, unknown))
app.run_polling()
