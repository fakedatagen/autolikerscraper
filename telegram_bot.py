import asyncio
import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from selenium_poster import run_posting_bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN environment variable must be set.")
    print("Get your token from @BotFather on Telegram and add it to Replit Secrets.")
    exit(1)

LINKS_FILE = "links.txt"

def extract_links(text):
    """Extract URLs from text, supporting both plain URLs and [img]URL[/img] format"""
    links = []
    
    img_tag_pattern = r'\[img\](https?://[^\]]+)\[/img\]'
    img_matches = re.findall(img_tag_pattern, text, re.IGNORECASE)
    links.extend(img_matches)
    
    text_without_tags = re.sub(img_tag_pattern, '', text, flags=re.IGNORECASE)
    url_pattern = r'https?://[^\s]+'
    plain_urls = re.findall(url_pattern, text_without_tags)
    links.extend(plain_urls)
    
    return [link.strip() for link in links if link.strip()]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = """
🤖 *Selenium Forum Bot*

I can help you automatically post images to your forum thread!

*Available Commands:*
/start - Show this welcome message
/add - Add image links to the queue (supports multiple links!)
/run - Start posting all queued links
/status - Check how many links are queued
/help - Show detailed command help

*Quick Start:*
Send links in BBCode format:
```
/add [img]https://i.ibb.co/abc/image1.jpg[/img]
[img]https://i.ibb.co/xyz/image2.jpg[/img]
```

Use /help for more examples and tips!
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
*Command Guide:*

📝 */add* - Add image links to the queue
   Supports multiple formats:
   • Plain URLs: `https://example.com/image.jpg`
   • BBCode format: `[img]https://example.com/image.jpg[/img]`
   • Multiple links at once (one per line)
   
   Example:
   ```
   /add [img]https://i.ibb.co/abc/image1.jpg[/img]
   [img]https://i.ibb.co/xyz/image2.jpg[/img]
   ```

🚀 */run* - Start posting all queued links
   The bot will post each link with a 10-second delay

📊 */status* - View queue status
   Shows how many links are waiting to be posted

💡 *Tips:*
• You can paste multiple [img] tags at once
• Mix plain URLs and [img] tags
• Links are posted in the order they were added
• Successfully posted links are automatically removed
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please provide links.\n\nUsage: `/add [img]URL[/img]` or `/add URL`\n\nYou can send multiple links at once!", parse_mode='Markdown')
        return
    
    full_text = " ".join(context.args)
    links = extract_links(full_text)
    
    if not links:
        await update.message.reply_text("❌ No valid links found. Please provide URLs in one of these formats:\n• `https://example.com/image.jpg`\n• `[img]https://example.com/image.jpg[/img]`", parse_mode='Markdown')
        return
    
    with open(LINKS_FILE, "a", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")
    
    if len(links) == 1:
        await update.message.reply_text(f"✅ Link added to queue!\n🔗 {links[0]}")
    else:
        link_preview = "\n".join([f"{i+1}. {link}" for i, link in enumerate(links[:3])])
        more_text = f"\n...and {len(links) - 3} more" if len(links) > 3 else ""
        await update.message.reply_text(f"✅ Added {len(links)} links to queue!\n\n{link_preview}{more_text}")

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
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Stopping bot...")
    finally:
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
