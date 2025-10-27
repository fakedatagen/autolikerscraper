# Selenium Bot Project

## Overview
This project contains a Selenium-based automation bot that logs into a forum website and posts content automatically. The bot runs in headless mode (no visible browser window).

## Project Structure
- `bot.py` - Main Selenium automation script
- `links.txt` - File containing image links to post (one per line)
- `.pythonlibs/` - Python virtual environment with dependencies

## Setup Complete
- Python 3.11 installed
- Selenium package installed
- Chromium and ChromeDriver installed for headless browsing

## How to Use
1. Add your image links to `links.txt`, one link per line
2. The bot will:
   - Log into the specified forum
   - Navigate to the thread
   - Post each link with formatted content
   - Remove posted links from the file
   - Wait between posts (configurable delay)

## Configuration
Edit `bot.py` to customize:
- `USERNAME` and `PASSWORD` - Login credentials
- `THREAD_URL` - Target thread URL
- `POST_DELAY` - Seconds to wait between posts (default: 10)
- Post content template (around line 73)

## Running the Bot
The bot is configured as a workflow and can be started/stopped using the workflow controls. It will process all links in `links.txt` and exit when complete.

## Important Notes
- Links are removed from `links.txt` after successful posting
- The bot runs in headless mode (no GUI)
- Make sure `links.txt` contains valid URLs before running
- Empty lines in `links.txt` are automatically skipped

## Last Updated
October 27, 2025
