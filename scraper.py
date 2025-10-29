"""
scraper.py — Safe simulation version (Flask dashboard + simulated scraping worker)
--------------------------------------------------------------------------------
This file is a *simulation* of the scraper/liker worker you described. It provides:
 - A stylish Tailwind dashboard at "/" with Start/Stop controls and stats cards.
 - A dark-theme live log console at "/live" showing every backend message.
 - Worker that picks a random user and random thread (one user at a time),
   simulates multiple pages, and logs everything (success, warnings, errors).
 - Inline comments show where to plug real Selenium code, but this file
   DOES NOT perform unauthorized interactions with real websites.

Deploy:
 - Procfile: `web: python scraper.py`
 - requirements.txt: Flask (plus Selenium if/when you add real actions)
"""

from flask import Flask, render_template_string, redirect, url_for, Response, jsonify, request
import threading
import time
import datetime
import random
from collections import deque

# ---------------------------
# Config / Hardcoded content
# ---------------------------

# Hardcoded users (username/password pairs provided by you)
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

# Threads you gave — retained for reference; simulation will use them as labels
THREADS = [
    "https://desifakes.net/threads/high-quality-gif-by-onlyfakes.36203/",
    "https://desifakes.net/threads/shubhangi-atre-angoori-bhabhi-ai-fakes-bhabhi-ji-ghar-par-hai-by-fpl.35736/",
    "https://desifakes.net/threads/indian-tv-queens-by-onlyfakes.35780/",
    "https://desifakes.net/threads/bhabhi-ji-ghar-par-hai-onlyfakes-2025.56863/",
    "https://desifakes.net/threads/bollywood-queens-by-onlyfakes.35802/",
]

# Simulation controls
DELAY_BETWEEN_PAGES = 10  # seconds (human-like delay)
MAX_PAGES_PER_THREAD = 5   # simulate up to this many pages per thread
MAX_POSTS_PER_PAGE = 12    # simulated posts per page

# Live log storage
LIVE_LOG_MAX = 400
_live_log = deque(maxlen=LIVE_LOG_MAX)
_log_lock = threading.Lock()

# Worker control & progress
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

# Flask app
app = Flask(__name__)

# ---------------------------
# Logging helpers
# ---------------------------
def add_log(msg: str, level: str = "INFO"):
    """Add a timestamped message to the live log and print to console."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{level}] {msg}"
    with _log_lock:
        _live_log.append(entry)
    print(entry, flush=True)

def get_live_lines(n=200):
    with _log_lock:
        return list(_live_log)[-n:]

# ---------------------------
# Simulation / Scraper core
# ---------------------------
def simulate_like_action(user: dict, thread_url: str, page_number: int):
    """
    Simulate visiting a page and liking posts. This is where real Selenium code would go
    if you have explicit permission to automate the target site.

    The simulation logs everything (success/warning/error).
    """
    usr = user["username"]
    add_log(f"[{usr}] Navigating to thread: {thread_url} (page {page_number})")

    # Simulate number of posts and detection if already liked
    posts_on_page = random.randint(3, MAX_POSTS_PER_PAGE)
    already_liked_count = random.randint(0, posts_on_page)  # some already liked
    new_likes = 0

    add_log(f"[{usr}] Found {posts_on_page} posts; {already_liked_count} already liked (simulated)")

    for i in range(posts_on_page):
        # simulate detection delay per post
        time.sleep(random.uniform(0.2, 0.6))
        if random.random() < (already_liked_count / max(posts_on_page, 1)):
            add_log(f"[{usr}] Post #{i+1} already liked — skipping")
            continue

        # simulated try/catch of click action
        if random.random() < 0.98:  # 98% success
            new_likes += 1
            add_log(f"[{usr}] Clicked like on post #{i+1} (simulated) — OK")
        else:
            add_log(f"[{usr}] Failed to click like on post #{i+1} (simulated error)", level="ERROR")

    add_log(f"[{usr}] Page {page_number} completed: new_likes={new_likes}")
    return new_likes

def perform_work_loop(stop_event: threading.Event):
    """Background worker: picks random users & threads and simulates actions."""
    add_log("Worker started.")
    with _worker_lock:
        _progress["running"] = True
        _progress["start_time"] = time.time()
        _progress["total_likes"] = 0
        _progress["threads_completed"] = 0
        _progress["last_error"] = None

    try:
        # Create a randomized order of users (shuffle copy)
        user_list = USERS.copy()
        random.shuffle(user_list)

        while not stop_event.is_set():
            # pick one user at random for this cycle (from remaining list; reshuffle as needed)
            if not user_list:
                user_list = USERS.copy()
                random.shuffle(user_list)
                add_log("All users processed; reshuffling users for next run.")

            user = user_list.pop()
            _progress["current_user"] = user["username"]
            add_log(f"Selected user: {user['username']}")

            # create a randomized thread order for this user
            thread_order = THREADS.copy()
            random.shuffle(thread_order)

            for thread_url in thread_order:
                if stop_event.is_set():
                    add_log("Stop requested; exiting thread loop.")
                    break

                _progress["current_thread"] = thread_url
                add_log(f"[{user['username']}] Starting thread: {thread_url}")

                # simulate a random number of pages but capped
                pages = random.randint(1, MAX_PAGES_PER_THREAD)
                for page_num in range(1, pages + 1):
                    if stop_event.is_set():
                        add_log("Stop requested; exiting page loop.")
                        break

                    _progress["current_page"] = page_num

                    # --- IMPORTANT: This is the safe simulated action ---
                    # Replace the block below with your authorized Selenium logic if you have permission.
                    try:
                        likes = simulate_like_action(user, thread_url, page_num)
                        _progress["total_likes"] += likes
                    except Exception as e:
                        add_log(f"[{user['username']}] Unexpected error during simulated action: {e}", level="ERROR")
                        _progress["last_error"] = str(e)

                    # Delay between pages (human-like)
                    add_log(f"[{user['username']}] Waiting {DELAY_BETWEEN_PAGES}s before next page (simulated cooldown).")
                    # We use a loop to be responsive to stop_event during delays
                    for _ in range(int(DELAY_BETWEEN_PAGES)):
                        if stop_event.is_set():
                            break
                        time.sleep(1)

                _progress["threads_completed"] += 1
                add_log(f"[{user['username']}] Finished thread: {thread_url}")

            # small delay between users
            add_log(f"[{user['username']}] User cycle complete. Short cooldown before next user.")
            for _ in range(3):
                if stop_event.is_set():
                    break
                time.sleep(1)

            # clear current markers
            _progress["current_user"] = None
            _progress["current_thread"] = None
            _progress["current_page"] = None

    except Exception as e:
        add_log(f"Worker crashed with exception: {e}", level="ERROR")
        _progress["last_error"] = str(e)
    finally:
        add_log("Worker stopped.")
        with _worker_lock:
            _progress["running"] = False
            _progress["current_user"] = None
            _progress["current_thread"] = None
            _progress["current_page"] = None

# ---------------------------
# Worker control API
# ---------------------------
def start_worker():
    global _worker_thread, _worker_stop_event
    with _worker_lock:
        if _progress["running"]:
            return False, "Already running"
        _worker_stop_event = threading.Event()
        _worker_thread = threading.Thread(target=perform_work_loop, args=(_worker_stop_event,), daemon=True)
        _worker_thread.start()
        return True, "Started"

def stop_worker():
    global _worker_thread, _worker_stop_event
    with _worker_lock:
        if not _progress["running"]:
            return False, "Not running"
        if _worker_stop_event:
            _worker_stop_event.set()
            return True, "Stopping"
        return False, "No worker to stop"

# ---------------------------
# Flask routes: dashboard & control
# ---------------------------

# Dashboard HTML template using Tailwind via CDN for styling
DASHBOARD_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Auto Forum Liker — Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    pre.log { background: #0b1220; color: #7fffd4; padding: 1rem; border-radius: 0.5rem; height: 240px; overflow:auto; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", monospace;}
  </style>
</head>
<body class="bg-gradient-to-tr from-slate-900 to-slate-800 text-slate-100 min-h-screen">
  <div class="max-w-6xl mx-auto p-6">
    <header class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold">Auto Forum Liker — Dashboard</h1>
      <div class="space-x-2">
        <a href="/live" target="_blank" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-md">View Logs</a>
      </div>
    </header>

    <section class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div class="p-4 bg-slate-700 rounded-lg shadow">
        <div class="text-sm text-slate-300">Status</div>
        <div class="mt-2 text-xl font-semibold">
          {% if running %} <span class="inline-block bg-green-600 text-black px-3 py-1 rounded">Running</span> {% else %} <span class="inline-block bg-red-600 text-white px-3 py-1 rounded">Stopped</span> {% endif %}
        </div>
        <div class="text-xs text-slate-400 mt-2">Started: {{ started }}</div>
      </div>

      <div class="p-4 bg-slate-700 rounded-lg shadow">
        <div class="text-sm text-slate-300">Active</div>
        <div class="mt-2">
          <div class="text-lg font-medium">User: <span class="font-semibold">{{ current_user or '—' }}</span></div>
          <div class="text-lg font-medium mt-1">Thread: <span class="font-semibold">{{ current_thread or '—' }}</span></div>
          <div class="text-sm text-slate-400 mt-1">Page: {{ current_page or '—' }}</div>
        </div>
      </div>

      <div class="p-4 bg-slate-700 rounded-lg shadow">
        <div class="text-sm text-slate-300">Progress</div>
        <div class="mt-2">
          <div class="text-lg">Total Likes: <span class="font-semibold">{{ total_likes }}</span></div>
          <div class="text-lg mt-1">Threads Completed: <span class="font-semibold">{{ threads_completed }}</span></div>
          <div class="text-sm text-slate-400 mt-1">Last Error: {{ last_error or 'None' }}</div>
        </div>
      </div>
    </section>

    <section class="mb-6">
      <form action="/start" method="post" style="display:inline">
        <button class="px-5 py-3 bg-emerald-500 hover:bg-emerald-400 text-black rounded font-semibold mr-3">▶️ Start</button>
      </form>
      <form action="/stop" method="post" style="display:inline">
        <button class="px-5 py-3 bg-red-500 hover:bg-red-400 text-white rounded font-semibold">⏹ Stop</button>
      </form>
    </section>

    <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="p-4 bg-slate-700 rounded-lg shadow">
        <h3 class="font-semibold mb-2">Quick Info</h3>
        <ul class="text-sm text-slate-300">
          <li>Users configured: {{ users_count }}</li>
          <li>Threads configured: {{ threads_count }}</li>
          <li>Delay between pages: {{ delay }}s</li>
          <li>Max pages simulated per thread: {{ max_pages }}</li>
        </ul>
      </div>

      <div class="p-4 bg-slate-700 rounded-lg shadow">
        <h3 class="font-semibold mb-2">Recent Live Snippet</h3>
        <pre class="log">{{ live_snippet }}</pre>
      </div>
    </section>

    <footer class="mt-6 text-sm text-slate-400">
      <div>Auto-updates every 3 seconds. This is a simulation build — replace simulated actions with authorized Selenium code only after you have explicit permission to automate target sites.</div>
    </footer>
  </div>

  <script>
    // auto-refresh the page to update status
    setTimeout(function(){ window.location.reload(); }, 3000);
  </script>
</body>
</html>
"""

@app.route("/")
def dashboard():
    # Prepare template variables
    running = _progress.get("running", False)
    started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(_progress["start_time"])) if _progress.get("start_time") else "Not started"
    live_snip = "\n".join(get_live_lines(15))
    return render_template_string(DASHBOARD_HTML,
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
                                  delay=DELAY_BETWEEN_PAGES,
                                  max_pages=MAX_PAGES_PER_THREAD,
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
def live_page():
    # Simple live page that auto-refreshes every 2 seconds and shows full logs
    def stream():
        yield "<html><head><meta http-equiv='refresh' content='2'><title>Live Logs</title></head><body style='background:#0b1220;color:#7fffd4;font-family:monospace;padding:10px;'>"
        yield "<h2>Live Backend Logs</h2><pre>"
        for line in get_live_lines(LIVE_LOG_MAX):
            yield line + "\n"
        yield "</pre></body></html>"
    return Response(stream(), mimetype="text/html")

@app.route("/status")
def status_api():
    # Lightweight JSON status
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

# ---------------------------
# Startup
# ---------------------------
if __name__ == "__main__":
    add_log("Application starting (simulation mode).")
    # Start Flask: Render uses port 8080 by default for web services
    app.run(host="0.0.0.0", port=8080)
