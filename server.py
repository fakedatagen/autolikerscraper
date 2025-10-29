import threading
import os
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
    os.system("python telegram_bot.py")

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
