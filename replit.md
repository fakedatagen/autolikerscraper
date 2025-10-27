# Selenium Bot Project with Telegram Control

## Overview
This project contains a Selenium-based automation bot that logs into a forum website and posts content automatically. The bot runs in headless mode (no visible browser window) and can be controlled via Telegram!

## Project Structure
- `telegram_bot.py` - Telegram bot for controlling the automation (main entry point)
- `selenium_poster.py` - Core Selenium automation logic
- `bot.py` - Legacy standalone script (still works)
- `links.txt` - File containing image links to post (one per line)
- `.pythonlibs/` - Python virtual environment with dependencies

## Setup Complete
- Python 3.11 installed
- Selenium package installed
- python-telegram-bot package installed
- Chromium and ChromeDriver installed for headless browsing

## How to Use via Telegram

### Getting Started
1. The Telegram bot is already running! Find your bot on Telegram using the username you created with @BotFather
2. Start a chat with your bot and send `/start` to see available commands

### Available Commands
- `/start` - Show welcome message and command list
- `/help` - Show detailed command help and examples
- `/add` - Add image links to the queue (supports multiple formats!)
  - Plain URL: `/add https://example.com/image.jpg`
  - BBCode format: `/add [img]https://i.ibb.co/abc/image.jpg[/img]`
  - Multiple links at once:
    ```
    /add [img]https://i.ibb.co/abc/image1.jpg[/img]
    [img]https://i.ibb.co/xyz/image2.jpg[/img]
    [img]https://i.ibb.co/def/image3.jpg[/img]
    ```
- `/status` - Check how many links are in the queue
- `/run` - Start posting all queued links (this triggers the Selenium bot)

### Workflow
1. Add links to the queue using `/add` command
   - Copy-paste multiple `[img]URL[/img]` tags in one message
   - The bot automatically extracts all URLs
2. Use `/status` to check your queue
3. Send `/run` to start posting
4. The bot will:
   - Log into the forum
   - Post each link with your custom template
   - Remove posted links from the queue
   - Wait 10 seconds between posts

### Link Format Support
The bot intelligently parses multiple link formats:
- **BBCode tags**: `[img]https://example.com/image.jpg[/img]` (recommended)
- **Plain URLs**: `https://example.com/image.jpg`
- **Multiple links**: Send several links in one message
- **Mixed formats**: Combine BBCode and plain URLs

## Alternative: Direct File Method
You can still add links directly to `links.txt` (one per line) and use `/run` to process them.

## Configuration

### Required Secrets (Stored in Replit Secrets)
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from @BotFather
- `FORUM_USERNAME` - Your forum username
- `FORUM_PASSWORD` - Your forum password

### Customization
Edit `selenium_poster.py` to customize:
- `THREAD_URL` - Target thread URL (line 11)
- `POST_DELAY` - Seconds to wait between posts (default: 10, line 13)
- Post content template (around line 54-62)

## Running the Bot
The Telegram bot is configured as a workflow and runs automatically when the project starts. It stays active and waits for your commands on Telegram.

## Important Notes
- Links are removed from `links.txt` after successful posting
- The Selenium bot runs in headless mode (no GUI)
- Posts are delayed by 10 seconds to avoid flooding
- You can control everything remotely via Telegram!
- Empty lines in `links.txt` are automatically skipped

## Last Updated
October 27, 2025 - Enhanced Telegram bot with multi-link support and BBCode [img] tag parsing
