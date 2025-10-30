import random
import time
import threading
from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime, timedelta
from collections import deque

# ========= CONFIG =========
app = Flask(__name__)

BASE_URL = "https://desifakes.net/login"
WAIT_TIMEOUT = 15
LIKE_BUTTON_SELECTOR = 'a.actionBar-action--reaction.reaction--1'

# Hardcoded user credentials
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
    {"username": "Bhaisahab789", "password": "Bhaisahab789@789"}
]

# Hardcoded thread URLs
START_URLS = [
    "https://desifakes.net/threads/high-quality-gif-by-onlyfakes.36203/",
    "https://desifakes.net/threads/shubhangi-atre-angoori-bhabhi-ai-fakes-bhabhi-ji-ghar-par-hai-by-fpl.35736/",
    "https://desifakes.net/threads/indian-tv-queens-by-onlyfakes.35780/",
    "https://desifakes.net/threads/bhabhi-ji-ghar-par-hai-onlyfakes-2025.56863/",
    "https://desifakes.net/threads/bollywood-queens-by-onlyfakes.35802/"
]

# Global state for UI and control
state = {
    "is_running": False,
    "current_user": "None",
    "current_thread": "None",
    "current_page": 0,
    "total_likes": 0,
    "start_time": None,
    "threads_completed": 0,
    "liked_urls": {}  # Store liked URLs per user
}
logs = deque(maxlen=200)  # Keep last 200 log messages
stop_event = threading.Event()

# ========= SELENIUM CONFIG =========
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
        log_message(f"❌ Error fetching thread pages for {start_url}: {str(e)}")
        return sorted(list(all_urls)), 1

# ========= LOGGING =========
def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.append(f"[{timestamp}] {message}")
    print(message)

# ========= SCRAPER LOGIC =========
def run_scraper():
    state["is_running"] = True
    state["start_time"] = datetime.now()
    log_message("🚀 Scraper started!")

    while not stop_event.is_set():
        # Randomly select a user
        user = random.choice(USERS)
        username = user["username"]
        password = user["password"]
        if username not in state["liked_urls"]:
            state["liked_urls"][username] = set()
        user_liked_urls = state["liked_urls"][username]
        state["current_user"] = username
        log_message(f"🔑 Starting session for {username}...")

        driver = create_driver()
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        overall_liked = 0

        try:
            # Login
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
                log_message(f"⚠️ Login failed for {username}.")
                driver.quit()
                continue

            log_message(f"✅ Logged in as {username}")

            # Randomly select a thread
            thread_url = random.choice(START_URLS)
            state["current_thread"] = thread_url.split('/')[-2]
            log_message(f"🔁 Processing thread: {state['current_thread']}")

            thread_urls, total_pages = get_all_thread_urls(driver, thread_url)
            unvisited = [url for url in thread_urls if url not in user_liked_urls]

            for idx, url in enumerate(unvisited, start=1):
                if stop_event.is_set():
                    break
                state["current_page"] = idx
                driver.get(url)
                log_message(f"📄 Visiting page {idx} of {state['current_thread']}")
                time.sleep(random.uniform(1.2, 2.0))
                like_buttons = driver.find_elements(By.CSS_SELECTOR, LIKE_BUTTON_SELECTOR)
                unliked = [btn for btn in like_buttons if "has-reaction" not in (btn.get_attribute("class") or "")]
                new_likes = 0

                for btn in unliked:
                    if stop_event.is_set():
                        break
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(random.uniform(0.3, 0.6))
                        btn.click()
                        new_likes += 1
                        overall_liked += 1
                        state["total_likes"] += 1
                        time.sleep(random.uniform(0.7, 1.2))
                    except Exception as e:
                        log_message(f"❌ Error clicking like: {str(e)}")

                user_liked_urls.add(url)
                log_message(f"💗 Liked {new_likes} posts on page {idx}")

            state["threads_completed"] += 1
            log_message(f"✅ Completed thread {state['current_thread']} (Total likes: {overall_liked})")
            state["current_thread"] = "None"
            state["current_page"] = 0

        except Exception as e:
            log_message(f"❌ Error for {username}: {str(e)}")

        finally:
            driver.quit()
            log_message(f"🏁 Session for {username} finished. Waiting 10s before next run...")
            for _ in range(10):
                if stop_event.is_set():
                    break
                time.sleep(1)

    state["is_running"] = False
    state["current_user"] = "None"
    state["current_thread"] = "None"
    state["current_page"] = 0
    log_message("🛑 Scraper stopped!")

# ========= FLASK ROUTES =========
@app.route('/')
def dashboard():
    runtime = "00:00:00"
    if state["start_time"] and state["is_running"]:
        elapsed = datetime.now() - state["start_time"]
        runtime = str(timedelta(seconds=elapsed.seconds))
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Scraper Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <meta http-equiv="refresh" content="3">
    </head>
    <body class="bg-gray-900 text-white min-h-screen p-6">
        <div class="max-w-4xl mx-auto">
            <h1 class="text-3xl font-bold text-center mb-6 bg-gradient-to-r from-purple-500 to-indigo-500 bg-clip-text text-transparent">Scraper Dashboard</h1>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
                <div class="bg-gray-800 p-4 rounded-lg shadow-lg">
                    <h2 class="text-lg font-semibold mb-2">Bot Status</h2>
                    <p class="text-2xl font-bold {{ 'text-green-500' if state['is_running'] else 'text-red-500' }}">
                        {{ 'Running' if state['is_running'] else 'Stopped' }}
                    </p>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg shadow-lg">
                    <h2 class="text-lg font-semibold mb-2">Current User</h2>
                    <p class="text-xl">{{ state['current_user'] }}</p>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg shadow-lg">
                    <h2 class="text-lg font-semibold mb-2">Current Thread</h2>
                    <p class="text-xl">{{ state['current_thread'] }}</p>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg shadow-lg">
                    <h2 class="text-lg font-semibold mb-2">Current Page</h2>
                    <p class="text-xl">{{ state['current_page'] }}</p>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg shadow-lg">
                    <h2 class="text-lg font-semibold mb-2">Total Likes</h2>
                    <p class="text-xl">{{ state['total_likes'] }}</p>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg shadow-lg">
                    <h2 class="text-lg font-semibold mb-2">Runtime</h2>
                    <p class="text-xl">{{ runtime }}</p>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg shadow-lg">
                    <h2 class="text-lg font-semibold mb-2">Threads Completed</h2>
                    <p class="text-xl">{{ state['threads_completed'] }}</p>
                </div>
            </div>
            <div class="flex gap-4 justify-center">
                <form method="POST" action="/start">
                    <button type="submit" class="px-6 py-3 bg-gradient-to-r from-green-400 to-blue-500 text-white font-bold rounded-lg shadow-md hover:from-green-500 hover:to-blue-600 disabled:opacity-50" {{ 'disabled' if state['is_running'] else '' }}>Start</button>
                </form>
                <form method="POST" action="/stop">
                    <button type="submit" class="px-6 py-3 bg-gradient-to-r from-red-400 to-orange-500 text-white font-bold rounded-lg shadow-md hover:from-red-500 hover:to-orange-600 disabled:opacity-50" {{ 'disabled' if not state['is_running'] else '' }}>Stop</button>
                </form>
                <a href="/live" class="px-6 py-3 bg-gradient-to-r from-purple-400 to-indigo-500 text-white font-bold rounded-lg shadow-md hover:from-purple-500 hover:to-indigo-600">View Logs</a>
            </div>
        </div>
    </body>
    </html>
    """, state=state, runtime=runtime)

@app.route('/live')
def live_logs():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Live Logs</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <meta http-equiv="refresh" content="2">
    </head>
    <body class="bg-gray-900 text-neon-green min-h-screen p-6">
        <div class="max-w-4xl mx-auto">
            <h1 class="text-3xl font-bold text-center mb-6 text-green-400">Live Logs</h1>
            <div class="bg-gray-800 p-4 rounded-lg shadow-lg h-[70vh] overflow-y-auto font-mono text-sm text-green-300">
                {% for log in logs %}
                    <p>{{ log }}</p>
                {% endfor %}
            </div>
            <div class="mt-4 flex justify-center">
                <a href="/" class="px-6 py-3 bg-gradient-to-r from-purple-400 to-indigo-500 text-white font-bold rounded-lg shadow-md hover:from-purple-500 hover:to-indigo-600">Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """, logs=logs)

@app.route('/start', methods=['POST'])
def start_scraper():
    if not state["is_running"]:
        stop_event.clear()
        threading.Thread(target=run_scraper, daemon=True).start()
    return dashboard()

@app.route('/stop', methods=['POST'])
def stop_scraper():
    if state["is_running"]:
        stop_event.set()
    return dashboard()

# ========= MAIN =========
if __name__ == "__main__":
    log_message("🟢 App started. Access dashboard at /")
    app.run(host="0.0.0.0", port=8080)
