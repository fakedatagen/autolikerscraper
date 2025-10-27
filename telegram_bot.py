import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from selenium_poster import run_posting_bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN environment variable must be set.")
    print("Get your token from @BotFather on Telegram and add it to Replit Secrets.")
    exit(1)

LINKS_FILE = "links.txt"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = """
🤖 *Selenium Forum Bot*

I can help you automatically post images to your forum thread!

*Available Commands:*
/start - Show this welcome message
/add <link> - Add an image link to the queue
/run - Start posting all queued links
/status - Check how many links are queued
/help - Show command help

*How to use:*
1. Add image links using /add command
2. Use /run to start posting
3. The bot will post each link and remove it from the queue
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
*Command Guide:*

📝 */add <link>* - Add a new image link
   Example: `/add https://example.com/image.jpg`

🚀 */run* - Start posting all queued links
   The bot will post each link with a 10-second delay

📊 */status* - View queue status
   Shows how many links are waiting to be posted

💡 *Tips:*
• You can add multiple links, one at a time
• Links are posted in the order they were added
• Successfully posted links are automatically removed
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please provide a link.\nUsage: /add <link>")
        return
    
    link = " ".join(context.args)
    
    if not link.startswith("http"):
        await update.message.reply_text("❌ Please provide a valid URL starting with http:// or https://")
        return
    
    with open(LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")
    
    await update.message.reply_text(f"✅ Link added to queue!\n🔗 {link}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(LINKS_FILE):
        await update.message.reply_text("📭 No links in queue. Use /add to add links!")
        return
    
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]
    
    if len(links) == 0:
        await update.message.reply_text("📭 No links in queue. Use /add to add links!")
    else:
        link_list = "\n".join([f"{i+1}. {link}" for i, link in enumerate(links[:5])])
        more_text = f"\n...and {len(links) - 5} more" if len(links) > 5 else ""
        await update.message.reply_text(f"📊 *Queue Status*\n\n{len(links)} link(s) waiting:\n\n{link_list}{more_text}", parse_mode='Markdown')

async def run_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Starting the posting bot... This may take a while.")
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run_posting_bot)
    
    await update.message.reply_text(result)

async def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_link))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("run", run_bot))
    
    print("🤖 Telegram bot is running...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(main())
