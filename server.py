import threading
import subprocess
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ AutoLikerScraper is running — Flask + Telegram bot active!"

@app.route('/ping')
def ping():
    print("⏰ Ping received on AutoLikerScraper!")
    return "Ping received successfully!", 200

def run_bot():
    process = subprocess.Popen(
        ["python", "telegram_bot.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    for line in process.stdout:
        print(f"[BOT] {line}", end="")

def run_scraper():
    process = subprocess.Popen(
        ["python", "scraper.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    for line in process.stdout:
        print(f"[SCRAPER] {line}", end="")

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=run_scraper, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
