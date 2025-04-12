import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

file = r"C:\Users\patyt\Downloads\googlemapsextractor\restaurants-in-nashville-tennessee-detailed-reviews.xlsx"
df = pd.read_excel(
    file)


import re



def extract_id(url):
    if pd.isna(url) or not isinstance(url, str):
        return None  # or whatever default value you want
    
    pattern = r"contrib/(\d+)/reviews"
    match = re.search(pattern, url)
    if match:
        number = match.group(1)
        return number
    return None
df['userid'] = df['reviewer_profile'].apply(lambda x: extract_id(x))


import os
import requests

def get_profile_image(driver, url, save_dir="images"):
    base_url = "https://www.google.com/maps/contrib/"
    search_url = base_url + str(url)
    try:
        driver.get(search_url)
        time.sleep(5)

        img = driver.find_element(By.CLASS_NAME, "Iv2Hbb")
        profile_img_url = img.get_attribute("src")


        # Save image
        response = requests.get(profile_img_url)
        if response.status_code == 200:
            os.makedirs(save_dir, exist_ok=True)
            img_path = os.path.join(save_dir, f"{url}.jpg")
            with open(img_path, "wb") as f:
                f.write(response.content)
        else:
            img_path = None

        return {
            "profile_url": search_url,
            "profile_id": url,
            "image_url": profile_img_url,
            "image_path": img_path
        }

    except Exception as e:
        return {
            "profile_url": search_url,
            "error": str(e)
        }
driver = webdriver.Chrome(options=options)
results = []

for url in uid[:10]:  
    result = get_profile_image(driver, url)
    results.append(result)

driver.quit()
