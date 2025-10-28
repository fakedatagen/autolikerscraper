# telegram_bot.py
import asyncio
import os
import re
import requests
import base64
import threading
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from selenium_poster import run_posting_bot

# ===============================================================
# ⚙️ Configuration
# ===============================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
IMGBB_API_KEY = "f37c8ba38be5be1f4893accca2aaea6d"
LINKS_FILE = "links.txt"

# Default post delay (seconds)
DEFAULT_POST_DELAY = 10
_post_delay_lock = threading.Lock()
_post_delay = DEFAULT_POST_DELAY  # in seconds

# Globals to manage run state
_run_future = None
_run_stop_event = None
_run_progress = {"running": False, "posted": 0, "total": 0, "current": None}
_run_lock = threading.Lock()

if not TELEGRAM_TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN environment variable must be set.")
    exit(1)


# ===============================================================
# 🤖 Telegram Command Handlers
# ===============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = f"""
🤖 *Selenium Forum Bot*

I can help you automatically post images to your forum thread!

*Available Commands:*
/start - Show this welcome message
/add <[img]link[/img]> - Add one or more image links
/run - Start posting all queued links
/list - Show full content of links.txt
/status - Show active posting task status
/stop - Stop the active posting task
/clear - Clear all queued links
/setdelay - Choose posting delay via buttons
/cleardelay - Reset delay to default (10 sec)
/help - Show command help

📸 *Bonus:* Send image(s) directly — I’ll upload them to imgbb and add them automatically!
"""
    await update.message.reply_text(welcome_message, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = f"""
*Command Guide:*

📝 */add [img]https://...[/img]* - Add one or more image links
🚀 */run* - Start posting queued links
📋 */list* - Show links.txt content
📊 */status* - Show posting progress
🛑 */stop* - Stop active posting
⏱️ */setdelay* - Choose post delay from buttons
🔁 */cleardelay* - Reset delay to default ({DEFAULT_POST_DELAY}s)
🧹 */clear* - Clear all links
📸 *Send images directly* - Auto upload to imgbb
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


# /add
async def add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()
    content = message_text[len("/add"):].strip()

    if not content:
        await update.message.reply_text(
            "❌ Please provide one or more [img] links.\nUsage:\n/add [img]https://...[/img]"
        )
        return

    parts = re.findall(r"\[img\].+?\[/img\]", content)
    if not parts:
        await update.message.reply_text(
            "❌ Invalid format. Only [img]https://...[/img] links are allowed.")
        return

    with open(LINKS_FILE, "a", encoding="utf-8") as f:
        for link in parts:
            f.write(link + "\n")

    await update.message.reply_text(f"✅ Added {len(parts)} link(s) to queue.")


# /list
async def list_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(LINKS_FILE):
        await update.message.reply_text(
            "📭 links.txt not found. Queue is empty.")
        return
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        await update.message.reply_text("📭 links.txt is empty. Queue is empty."
                                        )
    else:
        MAX_CHUNK = 4000
        if len(content) <= MAX_CHUNK:
            await update.message.reply_text(f"📄 *links.txt*:\n\n{content}",
                                            parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "📄 *links.txt* (sending in chunks):", parse_mode="Markdown")
            for i in range(0, len(content), MAX_CHUNK):
                await update.message.reply_text(content[i:i + MAX_CHUNK])


# /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with _run_lock:
        running = _run_progress.get("running", False)
        posted = _run_progress.get("posted", 0)
        total = _run_progress.get("total", 0)
        current = _run_progress.get("current", None)
    with _post_delay_lock:
        pd = _post_delay

    if running:
        txt = f"⚙️ *Posting ACTIVE*\n\nPosted: {posted}/{total}\nDelay: {pd}s\n"
        if current:
            txt += f"Current:\n{current}"
        await update.message.reply_text(txt, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"✅ No active posting. Delay: {pd}s",
                                        parse_mode="Markdown")


# /clear
async def clear_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(LINKS_FILE) or os.stat(LINKS_FILE).st_size == 0:
        await update.message.reply_text("📭 The queue is already empty.")
        return

    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        f.write("")

    await update.message.reply_text("🧹 All links have been cleared.")


# /run
async def run_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _run_future, _run_stop_event, _run_progress

    with _run_lock:
        already_running = _run_progress.get("running", False)

    if already_running:
        await update.message.reply_text(
            "❌ Only one posting session can run at a time.")
        return

    stop_event = threading.Event()
    progress = {"running": False, "posted": 0, "total": 0, "current": None}

    with _post_delay_lock:
        pd = _post_delay

    loop = asyncio.get_event_loop()
    await update.message.reply_text("🚀 Starting posting bot...")

    with _run_lock:
        _run_stop_event = stop_event
        _run_progress = progress

    fut = loop.run_in_executor(None, run_posting_bot, stop_event, progress, pd)

    with _run_lock:
        _run_future = fut

    async def waiter_and_report():
        try:
            result = await fut
            await update.message.reply_text(result)
        finally:
            with _run_lock:
                _run_future = None
                _run_stop_event = None
                _run_progress = {
                    "running": False,
                    "posted": 0,
                    "total": 0,
                    "current": None
                }

    asyncio.create_task(waiter_and_report())


# /stop
async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _run_stop_event, _run_future
    with _run_lock:
        stop_event = _run_stop_event
        fut = _run_future
        running = _run_progress.get("running", False)

    if not running or stop_event is None or fut is None:
        await update.message.reply_text("ℹ️ No active posting session.")
        return

    stop_event.set()
    await update.message.reply_text(
        "🛑 Stop requested. Bot will stop after current post.")


# ===============================================================
# ⏱️ Delay Controls
# ===============================================================
# /setdelay — show buttons
async def set_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("10s (default)", callback_data="delay_10"),
            InlineKeyboardButton("1m", callback_data="delay_60"),
            InlineKeyboardButton("5m", callback_data="delay_300"),
        ],
        [
            InlineKeyboardButton("15m", callback_data="delay_900"),
            InlineKeyboardButton("30m", callback_data="delay_1800"),
            InlineKeyboardButton("1h", callback_data="delay_3600"),
        ],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⏱️ Choose a new post delay:",
                                    reply_markup=markup)


# callback for delay buttons
async def delay_button_callback(update: Update,
                                context: ContextTypes.DEFAULT_TYPE):
    global _post_delay
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("delay_"):
        return
    value = int(data.split("_")[1])
    with _post_delay_lock:
        _post_delay = value

    await query.edit_message_text(f"✅ Post delay set to {_post_delay} seconds."
                                  )


# /cleardelay
async def clear_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _post_delay
    with _post_delay_lock:
        _post_delay = DEFAULT_POST_DELAY
    await update.message.reply_text(
        f"✅ Delay reset to default: {DEFAULT_POST_DELAY}s.")


# ===============================================================
# 📸 Handle image uploads
# ===============================================================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📸 Received image update...")
    uploaded_links = []
    try:
        if update.message.photo:
            media_files = update.message.photo
        elif update.message.document and update.message.document.mime_type.startswith(
                "image/"):
            media_files = [update.message.document]
        else:
            return

        await update.message.reply_text("📤 Uploading image(s) to imgbb...")

        for media in media_files:
            file = await media.get_file()
            file_path = f"/tmp/{file.file_unique_id}.jpg"
            await file.download_to_drive(file_path)
            with open(file_path, "rb") as img:
                b64 = base64.b64encode(img.read())
            r = requests.post(
                "https://api.imgbb.com/1/upload",
                data={
                    "key": IMGBB_API_KEY,
                    "image": b64
                },
            )
            if r.status_code == 200:
                url = r.json()["data"]["url"]
                bbcode = f"[img]{url}[/img]"
                uploaded_links.append(bbcode)
            else:
                print(f"❌ Upload failed: {r.text}")

        if uploaded_links:
            with open(LINKS_FILE, "a", encoding="utf-8") as f:
                for link in uploaded_links:
                    f.write(link + "\n")
            joined = "\n".join(uploaded_links)
            await update.message.reply_text(
                f"✅ Uploaded {len(uploaded_links)} image(s):\n\n{joined}")
        else:
            await update.message.reply_text(
                "⚠️ No valid uploads were completed.")
    except Exception as e:
        print(f"❌ Exception in handle_photo: {e}")
        await update.message.reply_text(f"⚠️ Error: {e}")


# ===============================================================
# 🚀 Main Entry Point
# ===============================================================
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add_link))
    app.add_handler(CommandHandler("list", list_links))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("clear", clear_links))
    app.add_handler(CommandHandler("run", run_bot))
    app.add_handler(CommandHandler("stop", stop_bot))
    app.add_handler(CommandHandler("setdelay", set_delay))
    app.add_handler(
        CallbackQueryHandler(delay_button_callback, pattern="^delay_"))
    app.add_handler(CommandHandler("cleardelay", clear_delay))

    # Image handler
    app.add_handler(
        MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))

    print("🤖 Telegram bot is running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Stopping bot gracefully...")
    finally:
        try:
            await app.updater.stop()
        except Exception:
            pass
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
