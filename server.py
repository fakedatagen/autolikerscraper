from flask import Flask
import threading
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    print("✅ [FLASK] AutoLikerScraper Flask route hit!")
    return "✅ AutoLikerScraper is running!", 200

@app.route('/ping')
def ping():
    print("⏰ [FLASK] Ping received on AutoLikerScraper!")
    return "Pong! AutoLikerScraper alive.", 200

def run_bot():
    print("🤖 [BOT] Starting telegram_bot.py...")
    try:
        subprocess.run(["python", "telegram_bot.py"], check=True)
    except Exception as e:
        print(f"❌ [BOT] Failed to start telegram_bot.py: {e}")

def run_scraper():
    print("🧠 [SCRAPER] Starting scraper.py...")
    try:
        subprocess.run(["python", "scraper.py"], check=True)
    except Exception as e:
        print(f"❌ [SCRAPER] Failed to start scraper.py: {e}")

if __name__ == "__main__":
    print("🚀 [MAIN] Starting Flask + Bot + Scraper threads...")
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=run_scraper, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
