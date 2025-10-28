# scraper.py (Replit-compatible version)
import sqlite3
import datetime
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# ======== CONFIG ========
BASE_URL = "https://desifakes.net/login"
WAIT_TIMEOUT = 15

START_URLS = [
    "https://desifakes.net/threads/high-quality-gif-by-onlyfakes.36203/",
    "https://desifakes.net/threads/shubhangi-atre-angoori-bhabhi-ai-fakes-bhabhi-ji-ghar-par-hai-by-fpl.35736/",
    "https://desifakes.net/threads/indian-tv-queens-by-onlyfakes.35780/",
    "https://desifakes.net/threads/bhabhi-ji-ghar-par-hai-onlyfakes-2025.56863/",
    "https://desifakes.net/threads/bollywood-queens-by-onlyfakes.35802/"
]

LIKE_BUTTON_SELECTOR = 'a.actionBar-action--reaction.reaction--1'
DB_PATH = "botdata.db"

# ======== DB HELPERS (SQLite) ========


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def get_liked_urls(conn, username):
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS LikedLinks (Username TEXT, URL TEXT, LikedAt TEXT)"
    )
    cur.execute("SELECT URL FROM LikedLinks WHERE Username=?", (username, ))
    return {row[0] for row in cur.fetchall()}


def record_like(conn, username, url):
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO LikedLinks (Username, URL, LikedAt) VALUES (?, ?, ?)",
        (username, url, datetime.datetime.utcnow().isoformat()))
    conn.commit()


def log_activity(conn, username, activity_type, thread_url=None, message=""):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ActivityLog (
            Username TEXT,
            ActivityType TEXT,
            ThreadURL TEXT,
            Message TEXT,
            LoggedAt TEXT
        )
    """)
    cur.execute(
        "INSERT INTO ActivityLog (Username, ActivityType, ThreadURL, Message, LoggedAt) VALUES (?, ?, ?, ?, ?)",
        (username, activity_type, thread_url, message,
         datetime.datetime.utcnow().isoformat()))
    conn.commit()


def get_all_users_from_db():
    users_list = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS Users (Username TEXT, Password TEXT)")
        cur.execute("SELECT Username, Password FROM Users")
        for row in cur.fetchall():
            users_list.append({"username": row[0], "password": row[1]})
        conn.close()
        print(f"✅ Fetched {len(users_list)} users from SQLite.")
        return users_list
    except Exception as e:
        print(f"❌ Error fetching users: {e}")
        return []


# ======== SELENIUM CONFIG ========


def create_driver():
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager
    import os

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Replit Chrome binary path
    options.binary_location = "/usr/bin/google-chrome-stable"

    # Explicitly point to chromedriver binary path (installed by webdriver-manager)
    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_all_thread_urls(driver, start_url):
    all_urls = {start_url}
    base_thread_url = start_url.split('/page-')[0].strip('/')
    max_page_number = 1

    try:
        driver.get(start_url)
        time.sleep(random.uniform(1, 2))
        page_text_elements = driver.find_elements(By.CSS_SELECTOR,
                                                  '.pageNav-page')
        for element in page_text_elements:
            if element.text.strip().isdigit():
                max_page_number = max(max_page_number,
                                      int(element.text.strip()))
        for i in range(2, max_page_number + 1):
            page_url = f"{base_thread_url}/page-{i}"
            all_urls.add(page_url)
        return sorted(list(all_urls)), max_page_number
    except Exception:
        return sorted(list(all_urls)), 1


# ======== MAIN EXECUTION ========


def run_scraper():
    users = get_all_users_from_db()
    if not users:
        print("⚠️ No users found in the Users table.")
        return

    for user in users:
        username = user["username"]
        password = user["password"]
        print(f"\n🔑 Starting session for {username}...")

        driver = create_driver()
        conn = get_db_connection()
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        user_liked_urls = get_liked_urls(conn, username)
        overall_liked = 0

        log_activity(conn, username, "USER_START", message="Session started.")

        try:
            # --- LOGIN ---
            driver.get(BASE_URL)
            username_input = wait.until(
                EC.presence_of_element_located((By.NAME, "login")))
            username_input.clear()
            username_input.send_keys(username)

            password_input = driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(password)
            driver.find_element(By.CSS_SELECTOR,
                                ".button--icon--login").click()

            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)

            if "login" in driver.current_url.lower():
                print(f"⚠️ Login failed for {username}.")
                log_activity(conn,
                             username,
                             "LOGIN_FAILED",
                             message="Login failed.")
                continue

            print(f"✅ Logged in as {username}")
            log_activity(conn, username, "LOGIN_SUCCESS", message="Logged in.")

            # --- AUTO LIKE ---
            for start_url in START_URLS:
                total_liked = 0
                thread_name = start_url.split('/')[-2]
                print(f"\n🔁 Thread: {thread_name}")
                log_activity(conn, username, "THREAD_START", start_url,
                             f"Started {thread_name}")

                thread_urls, total_pages = get_all_thread_urls(
                    driver, start_url)
                unvisited = [
                    url for url in thread_urls if url not in user_liked_urls
                ]

                for idx, url in enumerate(unvisited, start=1):
                    driver.get(url)
                    time.sleep(random.uniform(1.2, 2.0))
                    like_buttons = driver.find_elements(
                        By.CSS_SELECTOR, LIKE_BUTTON_SELECTOR)
                    unliked = [
                        btn for btn in like_buttons if "has-reaction" not in (
                            btn.get_attribute("class") or "")
                    ]
                    new_likes = 0

                    for btn in unliked:
                        try:
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});",
                                btn)
                            time.sleep(random.uniform(0.3, 0.6))
                            btn.click()
                            new_likes += 1
                            overall_liked += 1
                            total_liked += 1
                            time.sleep(random.uniform(0.7, 1.2))
                        except:
                            pass

                    record_like(conn, username, url)
                    log_activity(conn, username, "PAGE_FINISH", url,
                                 f"Liked {new_likes} new posts.")

                log_activity(conn, username, "THREAD_FINISH", start_url,
                             f"Total likes: {total_liked}")

        except Exception as e:
            print(f"❌ Error for {username}: {e}")
            log_activity(conn, username, "USER_ERROR", message=str(e))

        finally:
            log_activity(conn,
                         username,
                         "USER_FINISH",
                         message=f"Session done. Total likes: {overall_liked}")
            driver.quit()
            conn.close()


if __name__ == "__main__":
    run_scraper()
