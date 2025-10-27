from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os

def run_posting_bot():
    USERNAME = os.getenv("FORUM_USERNAME")
    PASSWORD = os.getenv("FORUM_PASSWORD")
    THREAD_URL = "https://desifakes.net/threads/imagination-into-reality-premium-fakes-by-onlyfakes.57085/"
    LINKS_FILE = "links.txt"
    POST_DELAY = 10

    if not USERNAME or not PASSWORD:
        return "❌ Error: FORUM_USERNAME and FORUM_PASSWORD environment variables must be set."

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://desifakes.net/login")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "login"))
        ).send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        driver.find_element(By.CSS_SELECTOR, ".button--icon--login").click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("✅ Logged in successfully!")

        if not os.path.exists(LINKS_FILE):
            return f"❌ Error: '{LINKS_FILE}' not found."

        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]

        if len(links) == 0:
            return "📭 No links to post. Add links using /add command or edit links.txt"

        print(f"🖼️ Found {len(links)} links to post.")
        posted_count = 0

        for index, img_link in enumerate(links, start=1):
            print(f"\n=== Posting #{index}: {img_link} ===")

            driver.get(THREAD_URL)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.fr-element.fr-view[contenteditable='true']"))
            )

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

            reply_box = driver.find_element(By.CSS_SELECTOR, "div.fr-element.fr-view[contenteditable='true']")
            driver.execute_script("arguments[0].scrollIntoView(true);", reply_box)
            reply_box.click()
            time.sleep(1)
            reply_box.clear()
            reply_box.send_keys(content)
            
            time.sleep(POST_DELAY)
            try:
                post_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button--icon--reply"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
                time.sleep(1)
                post_button.click()
                print(f"✅ Posted reply #{index} successfully!")
                posted_count += 1

                with open(LINKS_FILE, "r", encoding="utf-8") as file:
                    remaining_links = [line for line in file if line.strip() != img_link]

                with open(LINKS_FILE, "w", encoding="utf-8") as file:
                    file.writelines("\n".join(link.strip() for link in remaining_links) + "\n")

                print(f"🗑️ Deleted posted link from {LINKS_FILE}.")

            except Exception as e:
                print(f"⚠️ Could not post reply #{index}: {e}")

            print(f"⏳ Waiting {POST_DELAY} seconds before next post...")
            time.sleep(POST_DELAY)

        return f"🎉 Successfully posted {posted_count} out of {len(links)} links!"

    except Exception as e:
        return f"❌ Error during posting: {str(e)}"
    
    finally:
        driver.quit()

if __name__ == "__main__":
    result = run_posting_bot()
    print(result)
