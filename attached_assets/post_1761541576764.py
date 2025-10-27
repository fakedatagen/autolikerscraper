from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# ======== CONFIGURATION ========
USERNAME = "onlyfakes"
PASSWORD = "Ashish#123"
THREAD_URL = "https://desifakes.net/threads/imagination-into-reality-premium-fakes-by-onlyfakes.57085/" #"https://desifakes.net/threads/bhabhi-ji-ghar-par-hai-onlyfakes-2025.56863/"
LINKS_FILE = "links.txt"
POST_DELAY = 10  # seconds between posts

# ======== SELENIUM SETUP ========
#driver = webdriver.Chrome()
#driver.maximize_window()

# ======== SELENIUM SETUP (HEADLESS MODE) ========
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")               # Run Chrome in headless mode (no GUI)
options.add_argument("--disable-gpu")            # Disable GPU (recommended for headless)
options.add_argument("--window-size=1920,1080")  # Set window size so elements load properly
options.add_argument("--no-sandbox")             # Bypass OS security model
options.add_argument("--disable-dev-shm-usage")  # Prevent /dev/shm errors on Linux

driver = webdriver.Chrome(options=options)


# ======== LOGIN ========
driver.get("https://desifakes.net/login")

WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, "login"))
).send_keys(USERNAME)
driver.find_element(By.NAME, "password").send_keys(PASSWORD)
driver.find_element(By.CSS_SELECTOR, ".button--icon--login").click()

WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
print("✅ Logged in successfully!")

# ======== LOAD LINKS ========
if not os.path.exists(LINKS_FILE):
    print(f"❌ Error: '{LINKS_FILE}' not found.")
    driver.quit()
    exit()

with open(LINKS_FILE, "r", encoding="utf-8") as f:
    links = [line.strip() for line in f if line.strip()]

print(f"🖼️ Found {len(links)} links to post.")

# ======== POST LOOP ========
for index, img_link in enumerate(links, start=1):
    print(f"\n=== Posting #{index}: {img_link} ===")

    # Step 1: Open the thread
    driver.get(THREAD_URL)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.fr-element.fr-view[contenteditable='true']"))
    )

    # Step 2: Build post content dynamically
    content = f"""
[CENTER][SIZE=7][B]:devilish: Tammana Bhatia :devilish:[/B][/SIZE]
[HR][/HR]
{img_link}
[HR][/HR]
[IMG]https://i.ibb.co/NnTDLwH/Only-Fakes-1.gif[/IMG]
[HR][/HR]
[IMG]https://i.ibb.co/LtYrp2V/PLEASE-SHOW-YOUR-SUPPORT.gif[/IMG]
[HR][/HR]
[/CENTER]
""".strip()

    # Step 3: Input reply text
    reply_box = driver.find_element(By.CSS_SELECTOR, "div.fr-element.fr-view[contenteditable='true']")
    driver.execute_script("arguments[0].scrollIntoView(true);", reply_box)
    reply_box.click()
    time.sleep(1)
    reply_box.clear()
    reply_box.send_keys(content)
    
    # Step 4: Click “Post reply” button
    time.sleep(POST_DELAY)
    try:
        post_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button--icon--reply"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
        time.sleep(1)
        post_button.click()
        print(f"✅ Posted reply #{index} successfully!")

        # Step 5: Remove posted link from file
        with open(LINKS_FILE, "r", encoding="utf-8") as file:
            remaining_links = [line for line in file if line.strip() != img_link]

        with open(LINKS_FILE, "w", encoding="utf-8") as file:
            file.writelines("\n".join(link.strip() for link in remaining_links) + "\n")

        print(f"🗑️ Deleted posted link from {LINKS_FILE}.")

    except Exception as e:
        print(f"⚠️ Could not post reply #{index}: {e}")

    # Step 6: Wait before next post
    print(f"⏳ Waiting {POST_DELAY} seconds before next post...")
    time.sleep(POST_DELAY)

# ======== DONE ========
print("🎉 All posts done!")
driver.quit()
