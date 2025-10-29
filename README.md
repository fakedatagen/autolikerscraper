# 🕵️‍♂️ Auto Liker Scraper Tool

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Requests](https://img.shields.io/badge/Requests-Web%20Scraping-green)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-HTML%20Parser-yellow)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)

A blazing-fast **web scraper** that gathers like or reaction data from web pages and sends instant summaries to a **Telegram chat**.

---

## 🌟 Features
- 🔍 Extract post-like or reaction data  
- 📦 Outputs JSON or CSV format  
- 💬 Sends results and status updates to Telegram  
- 🧠 Modular structure (`scraper.py` + `telegram_notify.py`)  

---

## ⚙️ Installation

```bash
git clone https://github.com/yourusername/autolikerscraper.git
cd autolikerscraper
pip install -r requirements.txt
```

Set your Telegram credentials in `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

---

## ▶️ Run the Scraper

```bash
python scraper.py
```

Example Telegram alert:
```
📊 Scraping complete!
Post ID: 12345
Likes: 150
Top users: user1, user2, user3
```

---

## 📁 Project Structure
```
autolikerscraper/
├── scraper.py
├── telegram_notify.py
├── utils.py
└── requirements.txt
```

---

## 💡 Tips
- Add random delays to avoid rate limits  
- Combine with proxy rotation for large-scale scraping  
- Extend Telegram notifications for daily summaries  

---

## 📄 License
Licensed under the [MIT License](LICENSE)

**Scrape, analyze, and get notified — all in real-time via Telegram ⚙️**
