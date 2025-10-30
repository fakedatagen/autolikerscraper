#!/usr/bin/env python3
# scraper.py
# Single-file Flask app with a stylish dashboard and full real Selenium worker.
#
# - /         -> Dashboard (Tailwind-styled)
# - /start    -> Start background worker (POST)
# - /stop     -> Stop background worker (POST)
# - /live     -> Full live backend logs (auto-refresh)
# - /status   -> JSON status API
#
# This version uses REAL Selenium logic from your original code.
# Ensure you have permission to scrape and automate interactions on the site.

from flask import Flask, render_template_string, redirect, url_for, Response, jsonify, request
import threading
import time
import datetime
import random
from collections import deque
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# -----------------------
# Hardcoded configuration
# -----------------------

# USERS (hardcoded username:password pairs you provided)
USERS = [
    {"username": "aaravmehra", "password": "aaravmehra@789"},
    {"username": "kavyasharma", "password": "kavyasharma@789"},
    {"username": "nehapatel", "password": "nehapatel@789"},
    {"username": "arjunnair", "password": "arjunnair@789"},
    {"username": "diyaverma", "password": "diyaverma@789"},
    {"username": "ananyaiyer", "password": "ananyaiyer@789"},
    {"username": "karansingla", "password": "karansingla@789"},
    {"username": "rohanchopra", "password": "rohanchopra@789"},
    {"username": "priyamenon", "password": "priyamenon@789"},
    {"username": "varundesai", "password": "varundesai@789"},
    {"username": "snehareddy789", "password": "snehareddy@789"},
    {"username": "amitkhurana", "password": "amitkhurana@789"},
    {"username": "vivekmittal", "password": "vivekmittal@789"},
    {"username": "tanvirajput", "password": "tanvirajput@789"},
    {"username": "nikhilsethi", "password": "nikhilsethi@789"},
    {"username": "poojakohli", "password": "poojakohli@789"},
    {"username": "arnavtyagi", "password": "arnavtyagi@789"},
    {"username": "riyaagrawal", "password": "riyaagrawal@789"},
    {"username": "manavchatterjee", "password": "manavchatterjee@789"},
    {"username": "jainbabu", "password": "Ashish#123"},
    {"username": "hemu", "password": "Ashish#123"},
    {"username": "Pakaau789", "password": "Pakaau789@789"},
    {"username": "Goli789", "password": "Goli789@789"},
    {"username": "Laddoo789", "password": "Laddoo789@789"},
    {"username": "Tharki789", "password": "Tharki789@789"},
    {"username": "Dood789", "password": "Dood789@789"},
    {"username": "Masti789", "password": "Masti789@789"},
    {"username": "Rasam789", "password": "Rasam789@789"},
    {"username": "Dahivada789", "password": "Dahivada789@789"},
    {"username": "Gajarhalwa789", "password": "Gajarhalwa789@789"},
    {"username": "Chholekulche789", "password": "Chholekulche789@789"},
    {"username": "Panipuri789", "password": "Panipuri789@789"},
    {"username": "Khushboo789", "password": "Khushboo789@789"},
    {"username": "Tikichaat789", "password": "Tikichaat789@789"},
    {"username": "Dhokla789", "password": "Dhokla789@789"},
    {"username": "Gunda789", "password": "Gunda789@789"},
    {"username": "Wifi789", "password": "Wifi789@789"},
    {"username": "Hulk789", "password": "Hulk789@789"},
    {"username": "Khan789", "password": "Khan789@789"},
    {"username": "Ladduking789", "password": "Ladduking789@789"},
    {"username": "Oversmart789", "password": "Oversmart789@789"},
    {"username": "Dilli789", "password": "Dilli789@789"},
    {"username": "Baatein789", "password": "Baatein789@789"},
    {"username": "Chalta789", "password": "Chalta789@789"},
    {"username": "Pappu789", "password": "Pappu789@789"},
    {"username": "Bhaisahab789", "password": "Bhaisahab789@789"},
]

# THREADS (the list you provided)
THREADS = [
    "https://desifakes.net/threads/high-quality-gif-by-onlyfakes.36203/",
    "https://desifakes.net/threads/shubhangi-atre-angoori-bhabhi-ai-fakes-bhabhi-ji-ghar-par-hai-by-fpl.35736/",
    "https://desifakes.net/threads/indian-tv-queens-by-onlyfakes.35780/",
    "https://desifakes.net/threads/bhabhi-ji-ghar-par-hai-onlyfakes-2025.56863/",
    "https://desifakes.net/threads/bollywood-queens-by-onlyfakes.35802/",
]

# Constants from original
BASE_URL = "https://desifakes.net/login"
WAIT_TIMEOUT = 15
LIKE_BUTTON_SELECTOR = 'a.actionBar-action--reaction.reaction--1'
DELAY_BETWEEN_THREADS = 10  # seconds between threads

# Simulation controls (tweakable, but now real)
LIVE_LOG_MAX = 800           # keep last N log lines in memory

# -----------------------
# Internal runtime state
# -----------------------
_live_log = deque(maxlen=LIVE_LOG_MAX)
_log_lock = threading.Lock()

_worker_thread = None
_worker_stop_event = None
_worker_lock = threading.Lock()

_progress = {
    "running": False,
    "start_time": None,
    "current_user": None,
    "current_thread": None,
    "current_page": None,
    "total_likes": 0,
    "threads_completed": 0,
    "last_error": None,
}

app = Flask(__name__)

# -----------------------
# Logging helpers
# -----------------------
def add_log(message: str, level: str = "INFO"):
    """Add timestamped message to live log and print to stdout."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{level}] {message}"
    with _log_lock:
        _live_log.append(entry)
    # print to console so Render logs also contain it
    print(entry, flush=True)

def get_live_lines(n: int = 200):
    with _log_lock:
        return list(_live_log)[-n:]

# -----------------------
# Selenium helpers (from your original code)
# -----------------------
def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

def get_all_thread_urls(driver, start_url):
    all_urls = {start_url}
    base_thread_url = start_url.split('/page-')[0].strip('/')
    max_page_number = 1
    try:
        driver.get(start_url)
        time.sleep(random.uniform(1, 2))
        page_text_elements = driver.find_elements(By.CSS_SELECTOR, '.pageNav-page')
        for element in page_text_elements:
            if element.text.strip().isdigit():
                max_page_number = max(max_page_number, int(element.text.strip()))
        for i in range(2, max_page_number + 1):
            page_url = f"{base_thread_url}/page-{i}"
            all_urls.add(page_url)
        return sorted(list(all_urls)), max_page_number
    except Exception:
        return sorted(list(all_urls)), 1

def real_like_page(driver, user_liked_urls, url, username):
    """Real Selenium logic to visit page and like unliked posts."""
    driver.get(url)
    time.sleep(random.uniform(1.2, 2.0))
    like_buttons = driver.find_elements(By.CSS_SELECTOR, LIKE_BUTTON_SELECTOR)
    unliked = [btn for btn in like_buttons if "has-reaction" not in (btn.get_attribute("class") or "")]
    new_likes = 0
    for btn in unliked:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(random.uniform(0.3, 0.6))
            btn.click()
            new_likes += 1
            time.sleep(random.uniform(0.7, 1.2))
        except:
            pass
    user_liked_urls.add(url)
    return new_likes

# -----------------------
# Worker function (integrated real logic)
# -----------------------
def worker_loop(stop_event: threading.Event):
    """Main background worker: picks random users and threads, processes pages with real Selenium."""
    add_log("Worker starting...")
    with _worker_lock:
        _progress["running"] = True
        _progress["start_time"] = time.time()
        _progress["total_likes"] = 0
        _progress["threads_completed"] = 0
        _progress["last_error"] = None

    try:
        # shuffle user list to avoid deterministic order
        user_pool = USERS.copy()
        random.shuffle(user_pool)
        while not stop_event.is_set():
            if not user_pool:
                user_pool = USERS.copy()
                random.shuffle(user_pool)
                add_log("All users processed once — reshuffling user pool for another run.")

            user = user_pool.pop()
            username = user["username"]
            add_log(f"Selected user: {username}")
            _progress["current_user"] = username

            driver = create_driver()
            wait = WebDriverWait(driver, WAIT_TIMEOUT)
            user_liked_urls = set()  # In-memory per user session

            try:
                # Login
                driver.get(BASE_URL)
                username_input = wait.until(EC.presence_of_element_located((By.NAME, "login")))
                username_input.clear()
                username_input.send_keys(username)
                password_input = driver.find_element(By.NAME, "password")
                password_input.clear()
                password_input.send_keys(user["password"])
                driver.find_element(By.CSS_SELECTOR, ".button--icon--login").click()
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(2)
                if "login" in driver.current_url.lower():
                    add_log(f"Login failed for {username}.", level="ERROR")
                    continue
                add_log(f"Logged in as {username}.")

                # shuffle threads for this user
                thread_pool = THREADS.copy()
                random.shuffle(thread_pool)

                for thread_url in thread_pool:
                    if stop_event.is_set():
                        add_log("Stop requested — breaking thread loop.")
                        break

                    _progress["current_thread"] = thread_url.split('/')[-2]
                    add_log(f"[{username}] Starting thread: {thread_url}")

                    thread_urls, total_pages = get_all_thread_urls(driver, thread_url)
                    unvisited = [url for url in thread_urls if url not in user_liked_urls]

                    total_liked = 0
                    for idx, url in enumerate(unvisited, start=1):
                        if stop_event.is_set():
                            add_log("Stop requested — breaking page loop.")
                            break

                        _progress["current_page"] = idx

                        try:
                            likes = real_like_page(driver, user_liked_urls, url, username)
                            _progress["total_likes"] += likes
                            total_liked += likes
                            add_log(f"[{username}] Page {idx}/{len(unvisited)}: Liked {likes} new posts.")
                        except Exception as e:
                            add_log(f"[{username}] Exception on page {url}: {e}", level="ERROR")
                            _progress["last_error"] = str(e)

                        # wait between pages
                        for _ in range(DELAY_BETWEEN_THREADS):
                            if stop_event.is_set():
                                break
                            time.sleep(1)

                    _progress["threads_completed"] += 1
                    add_log(f"[{username}] Finished thread: {thread_url} - Total likes: {total_liked}")

                # small pause between users
                add_log(f"[{username}] Completed user cycle. Short cooldown.")
                for _ in range(3):
                    if stop_event.is_set():
                        break
                    time.sleep(1)

            finally:
                driver.quit()

            # clear per-cycle markers
            _progress["current_user"] = None
            _progress["current_thread"] = None
            _progress["current_page"] = None

    except Exception as e:
        add_log(f"Worker crashed with exception: {e}", level="ERROR")
        _progress["last_error"] = str(e)
    finally:
        add_log("Worker exiting and cleaning up.")
        with _worker_lock:
            _progress["running"] = False
            _progress["current_user"] = None
            _progress["current_thread"] = None
            _progress["current_page"] = None

# -----------------------
# Control helpers
# -----------------------
def start_worker():
    global _worker_thread, _worker_stop_event
    with _worker_lock:
        if _progress.get("running"):
            return False, "Already running"
        _worker_stop_event = threading.Event()
        _worker_thread = threading.Thread(target=worker_loop, args=(_worker_stop_event,), daemon=True)
        _worker_thread.start()
        return True, "Started"

def stop_worker():
    global _worker_stop_event
    with _worker_lock:
        if not _progress.get("running"):
            return False, "Not running"
        if _worker_stop_event:
            _worker_stop_event.set()
            return True, "Stopping"
        return False, "No worker event"

# -----------------------
# Flask UI templates
# -----------------------

DASH_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Auto Forum Liker — Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .muted { color: #94a3b8; }
    .card { background: rgba(15,23,42,0.6); border-radius: 12px; padding: 16px; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", monospace; }
    pre.snip { background: #071024; color: #d1fae5; padding:12px; border-radius:8px; height:220px; overflow:auto; }
  </style>
</head>
<body class="bg-gradient-to-tr from-slate-900 to-slate-800 text-slate-100 min-h-screen">
  <div class="max-w-6xl mx-auto p-6">
    <header class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold">Auto Forum Liker — Dashboard</h1>
        <p class="muted mt-1">Control and monitor the scraper (real Selenium mode)</p>
      </div>
      <div class="space-x-2">
        <a href="/live" target="_blank" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-md">View Logs</a>
      </div>
    </header>

    <section class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div class="card">
        <div class="text-sm muted">Status</div>
        <div class="mt-2">
          {% if running %}
            <span class="inline-block bg-green-400 text-black px-3 py-1 rounded font-bold">Running</span>
          {% else %}
            <span class="inline-block bg-red-500 text-white px-3 py-1 rounded font-bold">Stopped</span>
          {% endif %}
        </div>
        <div class="text-xs muted mt-2">Started: {{ started }}</div>
      </div>

      <div class="card">
        <div class="text-sm muted">Active</div>
        <div class="mt-2 text-lg">
          <div>User: <span class="font-semibold">{{ current_user or '—' }}</span></div>
          <div class="mt-1">Thread: <span class="font-semibold mono" style="word-break:break-all">{{ current_thread or '—' }}</span></div>
          <div class="mt-1 text-sm muted">Page: {{ current_page or '—' }}</div>
        </div>
      </div>

      <div class="card">
        <div class="text-sm muted">Progress</div>
        <div class="mt-2 text-lg">
          <div>Total Likes: <span class="font-semibold">{{ total_likes }}</span></div>
          <div class="mt-1">Threads Completed: <span class="font-semibold">{{ threads_completed }}</span></div>
          <div class="mt-1 text-sm muted">Last Error: {{ last_error or 'None' }}</div>
        </div>
      </div>
    </section>

    <section class="mb-6">
      <form action="/start" method="post" style="display:inline">
        <button class="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-black rounded font-semibold mr-3">▶️ Start</button>
      </form>
      <form action="/stop" method="post" style="display:inline">
        <button class="px-6 py-3 bg-red-500 hover:bg-red-400 text-white rounded font-semibold">⏹ Stop</button>
      </form>
    </section>

    <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="card
