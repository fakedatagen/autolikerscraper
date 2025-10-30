#!/usr/bin/env python3
# scraper.py
# Single-file Flask app with a stylish dashboard and Selenium-based scraper.
#
# - /         -> Dashboard (Tailwind-styled)
# - /start    -> Start background worker (POST)
# - /stop     -> Stop background worker (POST)
# - /live     -> Full live backend logs (auto-refresh)
# - /status   -> JSON status API
#
# This version uses Selenium to perform real scraping and liking activity.
# Deploy-ready for Render on port 8080.

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
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# -----------------------
# Hardcoded configuration
# -----------------------

# USERS (hardcoded username:password pairs as provided)
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

# THREADS (provided list of URLs)
THREADS = [
    "https://desifakes.net/threads/high-quality-gif-by-onlyfakes.36203/",
    "https://desifakes.net/threads/shubhangi-atre-angoori-bhabhi-ai-fakes-bhabhi-ji-ghar-par-hai-by-fpl.35736/",
    "https://desifakes.net/threads/indian-tv-queens-by-onlyfakes.35780/",
    "https://desifakes.net/threads/bhabhi-ji-ghar-par-hai-onlyfakes-2025.56863/",
    "https://desifakes.net/threads/bollywood-queens-by-onlyfakes.35802/",
]

# Configuration
BASE_URL = "https://desifakes.net/login"
LIKE_BUTTON_SELECTOR = 'a.actionBar-action--reaction.reaction--1'
WAIT_TIMEOUT = 15
DELAY_BETWEEN_THREADS = 10  # seconds between threads
LIVE_LOG_MAX = 200  # keep last N log lines in memory

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
    print(entry, flush=True)

def get_live_lines(n: int = 200):
    with _log_lock:
        return list(_live_log)[-n:]

# -----------------------
# Selenium setup
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
    except Exception as e:
        add_log(f"Error fetching thread pages for {start_url}: {e}", level="ERROR")
        return sorted(list(all_urls)), 1

def like_page(driver, user: dict, thread_url: str, page_num: int):
    """Visit a thread page and attempt to like unliked posts. Returns number of new likes."""
    username = user["username"]
    add_log(f"[{username}] Opening thread page {page_num} -> {thread_url}")
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    try:
        driver.get(thread_url)
        time.sleep(random.uniform(1.2, 2.0))
        like_buttons = driver.find_elements(By.CSS_SELECTOR, LIKE_BUTTON_SELECTOR)
        unliked = [
            btn for btn in like_buttons if "has-reaction" not in (btn.get_attribute("class") or "")
        ]
        new_likes = 0

        add_log(f"[{username}] Detected {len(like_buttons)} posts, {len(unliked)} unliked.")
        for btn in unliked:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(random.uniform(0.3, 0.6))
                btn.click()
                new_likes += 1
                add_log(f"[{username}] Clicked like on post — SUCCESS")
                time.sleep(random.uniform(0.7, 1.2))
            except Exception as e:
                add_log(f"[{username}] Error clicking like on post: {e}", level="ERROR")

        add_log(f"[{username}] Page {page_num} done. New likes on page: {new_likes}")
        return new_likes
    except Exception as e:
        add_log(f"[{username}] Error processing page {page_num}: {e}", level="ERROR")
        return 0

# -----------------------
# Worker function
# -----------------------
def worker_loop(stop_event: threading.Event):
    """Main background worker: picks random users and threads, processes pages, logs everything."""
    add_log("Worker starting...")
    with _worker_lock:
        _progress["running"] = True
        _progress["start_time"] = time.time()
        _progress["total_likes"] = 0
        _progress["threads_completed"] = 0
        _progress["last_error"] = None

    try:
        while not stop_event.is_set():
            user_pool = USERS.copy()
            random.shuffle(user_pool)
            if not user_pool:
                add_log("All users processed — reshuffling user pool for another run.")
                continue

            user = user_pool.pop()
            username = user["username"]
            password = user["password"]
            add_log(f"Selected user: {username}")
            _progress["current_user"] = username

            driver = create_driver()
            wait = WebDriverWait(driver, WAIT_TIMEOUT)

            # Login
            try:
                add_log(f"[{username}] Attempting login...")
                driver.get(BASE_URL)
                username_input = wait.until(EC.presence_of_element_located((By.NAME, "login")))
                username_input.clear()
                username_input.send_keys(username)
                password_input = driver.find_element(By.NAME, "password")
                password_input.clear()
                password_input.send_keys(password)
                driver.find_element(By.CSS_SELECTOR, ".button--icon--login").click()
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(2)

                if "login" in driver.current_url.lower():
                    add_log(f"[{username}] Login failed.", level="ERROR")
                    _progress["last_error"] = "Login failed"
                    driver.quit()
                    continue
                add_log(f"[{username}] Logged in successfully.")
            except Exception as e:
                add_log(f"[{username}] Login error: {e}", level="ERROR")
                _progress["last_error"] = str(e)
                driver.quit()
                continue

            # Process threads randomly
            thread_pool = THREADS.copy()
            random.shuffle(thread_pool)
            for thread_url in thread_pool:
                if stop_event.is_set():
                    add_log("Stop requested — breaking thread loop.")
                    break

                _progress["current_thread"] = thread_url
                add_log(f"[{username}] Starting thread: {thread_url}")

                thread_urls, total_pages = get_all_thread_urls(driver, thread_url)
                add_log(f"[{username}] Found {total_pages} pages for thread.")

                for idx, page_url in enumerate(thread_urls, start=1):
                    if stop_event.is_set():
                        add_log("Stop requested — breaking page loop.")
                        break

                    _progress["current_page"] = idx
                    likes = like_page(driver, user, page_url, idx)
                    _progress["total_likes"] += likes

                    # Delay between pages
                    add_log(f"[{username}] Sleeping before next page.")
                    for _ in range(5):
                        if stop_event.is_set():
                            break
                        time.sleep(1)

                _progress["threads_completed"] += 1
                add_log(f"[{username}] Finished thread: {thread_url}")

                # Delay between threads
                add_log(f"[{username}] Sleeping {DELAY_BETWEEN_THREADS}s before next thread.")
                for _ in range(DELAY_BETWEEN_THREADS):
                    if stop_event.is_set():
                        break
                    time.sleep(1)

            driver.quit()
            add_log(f"[{username}] Session completed. Short cooldown before next user.")
            for _ in range(3):
                if stop_event.is_set():
                    break
                time.sleep(1)

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
        <p class="muted mt-1">Control and monitor the scraper</p>
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
      <div class="card">
        <h3 class="font-semibold mb-2">Quick Info</h3>
        <ul class="text-sm muted space-y-1">
          <li>Users configured: <strong>{{ users_count }}</strong></li>
          <li>Threads configured: <strong>{{ threads_count }}</strong></li>
          <li>Delay between threads: <strong>{{ delay }}s</strong></li>
        </ul>
      </div>

      <div class="card">
        <h3 class="font-semibold mb-2">Recent logs</h3>
        <pre class="snip mono">{{ live_snippet }}</pre>
      </div>
    </section>

    <footer class="mt-6 text-sm muted">
      Auto-refresh every 3 seconds. Deploy-ready for Render.
    </footer>
  </div>

  <script>
    // reload every 3s to update dashboard values
    setTimeout(()=>{ window.location.reload(); }, 3000);
  </script>
</body>
</html>
"""

LIVE_HTML_HEAD = """
<html><head><title>Live Logs</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{background:#0b1220;color:#7fffd4;font-family:monospace;padding:10px}
pre{white-space:pre-wrap;word-break:break-word}
</style>
</head><body>
<h2>Live Backend Logs</h2>
<pre>
"""

LIVE_HTML_TAIL = """
</pre>
<script>
  // reload every 2s to update logs
  setTimeout(()=>{ window.location.reload(); }, 2000);
</script>
</body></html>
"""

# -----------------------
# Flask routes
# -----------------------
@app.route("/", methods=["GET"])
def dashboard():
    running = _progress.get("running", False)
    started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(_progress["start_time"])) if _progress.get("start_time") else "Not started"
    live_snip = "\n".join(get_live_lines(20))
    return render_template_string(DASH_HTML,
                                 running=running,
                                 started=started,
                                 current_user=_progress.get("current_user"),
                                 current_thread=_progress.get("current_thread"),
                                 current_page=_progress.get("current_page"),
                                 total_likes=_progress.get("total_likes"),
                                 threads_completed=_progress.get("threads_completed"),
                                 last_error=_progress.get("last_error"),
                                 users_count=len(USERS),
                                 threads_count=len(THREADS),
                                 delay=DELAY_BETWEEN_THREADS,
                                 live_snippet=live_snip)

@app.route("/start", methods=["POST"])
def http_start():
    ok, msg = start_worker()
    add_log(f"HTTP /start called -> {msg}")
    return redirect(url_for("dashboard"))

@app.route("/stop", methods=["POST"])
def http_stop():
    ok, msg = stop_worker()
    add_log(f"HTTP /stop called -> {msg}")
    return redirect(url_for("dashboard"))

@app.route("/live")
def live():
    lines = get_live_lines(LIVE_LOG_MAX)
    content = LIVE_HTML_HEAD + "\n".join(lines) + LIVE_HTML_TAIL
    return Response(content, mimetype="text/html")

@app.route("/status")
def status():
    uptime = 0
    if _progress.get("start_time"):
        uptime = int(time.time() - _progress["start_time"])
    return jsonify({
        "running": _progress.get("running", False),
        "current_user": _progress.get("current_user"),
        "current_thread": _progress.get("current_thread"),
        "current_page": _progress.get("current_page"),
        "total_likes": _progress.get("total_likes"),
        "threads_completed": _progress.get("threads_completed"),
        "uptime_seconds": uptime,
        "last_error": _progress.get("last_error"),
    })

# -----------------------
# Startup
# -----------------------
if __name__ == "__main__":
    add_log("Application starting with Selenium integration.")
    # Run Flask app (Render uses port 8080)
    app.run(host="0.0.0.0", port=8080)
