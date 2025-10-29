# telegram_bot.py
import asyncio
import os
import sys
import threading
import sqlite3
import datetime
import html
import time
from flask import Flask, Response
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from scraper import run_scraper

DB_PATH = "botdata.db"
TELEGRAM_TOKEN = "8379824269:AAFNf9RsAHc2E2gIGHokPSsF-oDFwiJK0lo"

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN missing in secrets!")
    sys.exit(1)

_run_lock = threading.Lock()
_run_progress = {"running": False}
_run_future = None
_run_stop_event = None

# ---------- Live behaviour log ----------
live_output = []

def add_output(message: str):
    """Add live behaviour message visible on /live page."""
    timestamp = time.strftime("[%H:%M:%S]")
    entry = f"{timestamp} | {message}"
    print(entry)
    live_output.append(entry)
    if len(live_output) > 200:
        live_output.pop(0)

# ---------- Flask live log server ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running — visit /live for live backend activity.", 200

@app.route('/live')
def live():
    def stream():
        yield "<html><head><meta http-equiv='refresh' content='3'></head><body>"
        yield "<h2>🚀 Live Bot Activity</h2><pre style='font-size:14px;'>"
        for line in live_output[-100:]:
            yield line + "\n"
        yield "</pre></body></html>"
    return Response(stream(), mimetype='text/html')

def run_flask():
    add_output("🌐 Flask live monitor starting on port 8080...")
    app.run(host="0.0.0.0", port=8080)

# ---------- DB helpers ----------
def get_dashboard_data():
    data = {
        "users": 0,
        "threads": 0,
        "likes": 0,
        "active_today": 0,
        "last": None
    }
    if not os.path.exists(DB_PATH):
        return data
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(
            "CREATE TABLE IF NOT EXISTS ActivityLog (Username TEXT, ActivityType TEXT, ThreadURL TEXT, Message TEXT, LoggedAt TEXT)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS Users (Username TEXT, Password TEXT)")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS LikedLinks (Username TEXT, URL TEXT, LikedAt TEXT)"
        )

        cur.execute("SELECT COUNT(*) FROM Users")
        data["users"] = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(DISTINCT ThreadURL) FROM ActivityLog WHERE ThreadURL IS NOT NULL"
        )
        data["threads"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM LikedLinks")
        data["likes"] = cur.fetchone()[0]

        today = datetime.date.today().isoformat()
        cur.execute(
            "SELECT COUNT(DISTINCT Username) FROM ActivityLog WHERE LoggedAt LIKE ?",
            (f"{today}%", ))
        data["active_today"] = cur.fetchone()[0]

        cur.execute(
            "SELECT Username, ActivityType, ThreadURL, Message, LoggedAt FROM ActivityLog ORDER BY ROWID DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            username, activity, thread, message, logged_at = row
            thread_name = thread.split("/")[-2] if thread else "N/A"
            data["last"] = {
                "user": username,
                "activity": activity,
                "thread": thread_name,
                "message": message,
                "time": logged_at
            }

        conn.close()

    except Exception as e:
        add_output(f"DB error: {e}")
    return data


def clear_logs():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM ActivityLog")
        conn.commit()
        conn.close()
        return "🧹 Logs cleared successfully!"
    except Exception as e:
        return f"❌ Failed to clear logs: {e}"


# ---------- Bot command handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = ("<b>🤖 Forum AutoLiker Bot</b>\n\n"
           "/run - Start scraper\n"
           "/stop - Stop scraper\n"
           "/status - Show dashboard\n"
           "/clearlogs - Clear activity logs\n"
           "/help - Show this message\n")
    add_output(f"/start command from {update.effective_user.username}")
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_output(f"/help command from {update.effective_user.username}")
    await start(update, context)


async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _run_future, _run_stop_event
    with _run_lock:
        if _run_progress.get("running"):
            await update.message.reply_text("⚙️ Scraper already running.")
            return
        _run_progress["running"] = True

    await update.message.reply_text("🚀 Starting scraper in background...")
    add_output(f"Scraper started by {update.effective_user.username}")

    loop = asyncio.get_event_loop()
    stop_event = threading.Event()
    _run_stop_event = stop_event

    def scraper_task():
        try:
            add_output("Scraper thread executing...")
            return run_scraper(stop_event, _run_progress)
        except Exception as e:
            add_output(f"❌ Scraper crashed: {e}")
            return f"❌ Scraper crashed: {e}"

    _run_future = loop.run_in_executor(None, scraper_task)

    async def watcher():
        try:
            result = await _run_future
            await update.message.reply_text(result)
        finally:
            with _run_lock:
                _run_progress["running"] = False
                _run_stop_event = None
            add_output("Scraper finished execution.")

    asyncio.create_task(watcher())

    async def live_status():
        await asyncio.sleep(30)
        while _run_progress.get("running"):
            data = get_dashboard_data()
            last = data["last"]
            if last:
                thread_esc = html.escape(last["thread"])
                message_esc = html.escape(str(last["message"]))
                await update.message.reply_text(
                    f"<b>⚙️ Live Status</b>\n👥 Users: {data['users']}\n🧵 Threads: {data['threads']}\n❤️ Likes: {data['likes']}\n\n"
                    f"<b>Last</b>\n👤 {html.escape(last['user'])}\n🧩 {thread_esc}\n💬 {html.escape(last['activity'])}\n💭 {message_esc}\n🕒 {html.escape(str(last['time']))}",
                    parse_mode=ParseMode.HTML)
            await asyncio.sleep(30)

    asyncio.create_task(live_status())


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_output(f"/stop command from {update.effective_user.username}")
    await update.message.reply_text(
        "🛑 Force stop requested — terminating now...")
    os._exit(0)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_dashboard_data()

    if data["last"]:
        last_info = (f"<b>Last Activity:</b>\n"
                     f"👤 {html.escape(data['last']['user'])}\n"
                     f"🧩 {html.escape(data['last']['thread'])}\n"
                     f"💬 {html.escape(data['last']['activity'])}\n"
                     f"💭 {html.escape(data['last']['message'])}\n"
                     f"🕒 {html.escape(data['last']['time'])}")
    else:
        last_info = "No recent activity recorded."

    status = "🟢 Running" if _run_progress.get("running") else "🔴 Stopped"
    msg = (f"<b>📊 Bot Dashboard</b>\n\n"
           f"Status: **{status}**\n"
           f"👥 Users in DB: **{data['users']}**\n"
           f"🧵 Total Threads Logged: **{data['threads']}**\n"
           f"❤️ Total Likes Logged: **{data['likes']}**\n"
           f"🏃 Active Users Today: **{data['active_today']}**\n\n"
           f"{last_info}")

    add_output(f"/status command from {update.effective_user.username}")
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def clearlogs_command(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    add_output(f"/clearlogs command from {update.effective_user.username}")
    result = clear_logs()
    await update.message.reply_text(result)


# ---------- main ----------
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    add_output("🌐 Flask live monitor started.")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("run", run_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("clearlogs", clearlogs_command))

    add_output("🤖 Telegram bot initializing...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    try:
        add_output("🟢 Telegram bot polling started.")
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        add_output("🛑 Telegram bot stopping...")
    finally:
        await app.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        add_output("Exiting...")
        print("Exiting...")
