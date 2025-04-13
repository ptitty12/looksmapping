import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from queue import Queue
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time



# Config
BASE_URL = "https://www.google.com/maps/contrib/"
SAVE_DIR = "images"
MAX_WORKERS = 8  # adjust based on RAM/CPU
os.makedirs(SAVE_DIR, exist_ok=True)

# Track already processed images
def get_processed_ids():
    return {filename.split('_')[0] for filename in os.listdir(SAVE_DIR) if filename.endswith('.jpg')}

# Create Chrome driver pool
def make_driver():
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return uc.Chrome(options=options)

driver_pool = Queue()
for _ in range(MAX_WORKERS):
    driver_pool.put(make_driver())

driver_lock = Lock()  # Optional if using only pool

def get_profile_image(profile_id):
    if f"{profile_id}.jpg" in os.listdir(SAVE_DIR):
        return {"url": profile_id, "skipped": True}

    driver = driver_pool.get()
    try:
        driver.get(BASE_URL + str(profile_id))
        img = WebDriverWait(driver, 6).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Iv2Hbb"))
        )
        profile_img_url = img.get_attribute("src")

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(profile_img_url, headers=headers, timeout=10)

        if response.status_code == 200:
            img_path = os.path.join(SAVE_DIR, f"{profile_id}.jpg")
            with open(img_path, "wb") as f:
                f.write(response.content)
            return {"url": profile_id, "success": True, "image_path": img_path}
        else:
            return {"url": profile_id, "success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        return {"url": profile_id, "success": False, "error": str(e)}

    finally:
        driver_pool.put(driver)  # return driver to pool

# Runner
def run_parallel(uid_list, max_workers=MAX_WORKERS):
    processed = get_processed_ids()
    to_process = [uid for uid in uid_list if uid not in processed]

    print(f"Skipping {len(processed)} already downloaded profiles.")
    print(f"Starting scrape of {len(to_process)} new profiles...")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(get_profile_image, uid) for uid in to_process]
        for i, future in enumerate(futures, 1):
            result = future.result()
            results.append(result)
            if i % 100 == 0:
                print(f"[INFO] {i} profiles processed... {datetime.now()}")

    return results

results = run_parallel(uid, max_workers=10)

