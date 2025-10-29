#!/usr/bin/env python3
# scraper.py
# Single-file Flask app with a stylish dashboard and full simulation worker.
#
# - /         -> Dashboard (Tailwind-styled)
# - /start    -> Start background worker (POST)
# - /stop     -> Stop background worker (POST)
# - /live     -> Full live backend logs (auto-refresh)
# - /status   -> JSON status API
#
# This version SIMULATES scraping/liking activity and logs every event.
# Replace simulated blocks with authorized Selenium logic only when you have permission.

from flask import Flask, render_template_string, redirect, url_for, Response, jsonify, request
import threading
import time
import datetime
import random
from collections import deque

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

# Simulation controls (tweakable)
DELAY_BETWEEN_PAGES = 10     # seconds between pages (human-like)
MAX_PAGES_PER_THREAD = 6     # max pages to simulate per thread
MAX_POSTS_PER_PAGE = 12      # simulated posts per page
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
# Simulation core (where real Selenium would be placed)
# -----------------------
def simulated_like_page(user: dict, thread_url: str, page_num: int):
    """
    Simulate visiting a thread page and trying to like posts.
    Returns number of new likes on that page.
    Detailed logs of all steps are written via add_log().
    """
    username = user["username"]
    add_log(f"[{username}] Opening thread page {page_num} -> {thread_url}")

    # simulate number of posts and already-liked count
    posts_on_page = random.randint(3, MAX_POSTS_PER_PAGE)
    already_liked = random.randint(0, posts_on_page)  # random
    new_likes = 0

    add_log(f"[{username}] Detected {posts_on_page} posts (simulated). {already_liked} already liked.")

    for i in range(1, posts_on_page + 1):
        # small per-post processing delay and responsiveness to stop
        for _ in range( max(1, int(random.uniform(0.2, 0.6) * 10)) ):
            time.sleep(0.01)
        # simulate a check whether this post is already liked
        if random.random() < (already_liked / max(posts_on_page, 1)):
            add_log(f"[{username}] Post #{i} already liked — skipping", level="DEBUG")
            continue

        # simulate clicking
        if random.random() < 0.97:
            new_likes += 1
            add_log(f"[{username}] Clicked like on post #{i} — SUCCESS")
            # small human-like delay
            time.sleep(random.uniform(0.3, 0.9))
        else:
            add_log(f"[{username}] Error clicking like on post #{i} (simulated)", level="ERROR")

    add_log(f"[{username}] Page {page_num} done. New likes on page: {new_likes}")
    return new_likes

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
        # shuffle user list to avoid deterministic order
        user_pool = USERS.copy()
        random.shuffle(user_pool)
        while not stop_event.is_set():
            if not user_pool:
                user_pool = USERS.copy()
                random.shuffle(user_pool)
                add_log("All users processed once — reshuffling user pool for another run.")

            user = user_pool.pop()
            add_log(f"Selected user: {user['username']}")
            _progress["current_user"] = user["username"]

            # shuffle threads for this user
            thread_pool = THREADS.copy()
            random.shuffle(thread_pool)

            for thread_url in thread_pool:
                if stop_event.is_set():
                    add_log("Stop requested — breaking thread loop.")
                    break

                _progress["current_thread"] = thread_url
                add_log(f"[{user['username']}] Starting thread: {thread_url}")

                pages_to_visit = random.randint(1, MAX_PAGES_PER_THREAD)
                for page_num in range(1, pages_to_visit + 1):
                    if stop_event.is_set():
                        add_log("Stop requested — breaking page loop.")
                        break

                    _progress["current_page"] = page_num

                    # === HERE you would insert your real Selenium action if authorized ===
                    # For simulation we call simulated_like_page which creates detailed logs.
                    try:
                        likes = simulated_like_page(user, thread_url, page_num)
                        _progress["total_likes"] = _progress.get("total_likes", 0) + likes
                    except Exception as e:
                        add_log(f"[{user['username']}] Exception during page work: {e}", level="ERROR")
                        _progress["last_error"] = str(e)

                    # wait between pages with early-stop responsiveness
                    add_log(f"[{user['username']}] Sleeping {DELAY_BETWEEN_PAGES}s before next page (simulated cooldown).")
                    for _ in range(DELAY_BETWEEN_PAGES):
                        if stop_event.is_set():
                            break
                        time.sleep(1)

                _progress["threads_completed"] = _progress.get("threads_completed", 0) + 1
                add_log(f"[{user['username']}] Finished thread: {thread_url}")

            # small pause between users
            add_log(f"[{user['username']}] Completed user cycle. Short cooldown.")
            for _ in range(3):
                if stop_event.is_set():
                    break
                time.sleep(1)

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
        <p class="muted mt-1">Control and monitor the scraper (simulation mode)</p>
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
          <li>Delay between pages: <strong>{{ delay }}s</strong></li>
          <li>Max pages per thread: <strong>{{ max_pages }}</strong></li>
        </ul>
      </div>

      <div class="card">
        <h3 class="font-semibold mb-2">Recent logs</h3>
        <pre class="snip mono">{{ live_snippet }}</pre>
      </div>
    </section>

    <footer class="mt-6 text-sm muted">
      Auto-refresh every 3 seconds. This app is running in simulation mode. Replace the simulation with authorized Selenium steps only after you have permission.
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
def live():
    # return full live log page auto-refreshing
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
    add_log("Application starting in SIMULATION mode.")
    # Run Flask app (Render uses port 8080)
    app.run(host="0.0.0.0", port=8080)
