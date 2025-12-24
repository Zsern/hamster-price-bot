import os
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ===================== CONFIG =====================
STAR_PETS_URL = "https://starpets.gg/adopt-me/shop/pet/hamster/24098"
THRESHOLD = 0.26  # Alert if normal hamster price <= this
ALERT_COOLDOWN = timedelta(hours=3)

# GitHub Secret
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

STATE_FILE = "last_alert.txt"

# ===================== HELPERS =====================
def now_ts():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

def load_last_alert():
    try:
        with open(STATE_FILE, "r") as f:
            return datetime.fromisoformat(f.read().strip())
    except:
        return None

def save_last_alert(ts):
    with open(STATE_FILE, "w") as f:
        f.write(ts.isoformat())

def can_alert():
    last = load_last_alert()
    if last is None:
        return True
    return datetime.utcnow() - last >= ALERT_COOLDOWN

def send_discord(message: str):
    if not DISCORD_WEBHOOK_URL:
        print("[WARN] Discord webhook not set")
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
    except Exception as e:
        print("[WARN] Discord send failed:", e)

# ===================== SELENIUM SETUP =====================
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")

driver = webdriver.Chrome(options=chrome_options)

# ===================== SCRAPER =====================
def get_lowest_normal_price():
    driver.get(STAR_PETS_URL)
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "_content_top_right_2ox1k_243"))
        )
    except:
        print("[WARN] Best price container not found.")
        return None

    soup = BeautifulSoup(driver.page_source, "html.parser")
    container = soup.find("div", class_="_content_top_right_2ox1k_243")
    if not container:
        print("[WARN] Container missing.")
        return None

    price_span = container.find("span", itemprop="price")
    if not price_span:
        print("[WARN] Price span not found.")
        return None

    try:
        return float(price_span["content"])
    except:
        return None

# ===================== MAIN =====================
print("[INFO] Normal Hamster Price Alert Bot started!")

price = get_lowest_normal_price()
ts = now_ts()
print(f"[INFO] Checked at {ts} | Normal Hamster Price: {price}")

if price is not None and price <= THRESHOLD and can_alert():
    msg = (
        "🐹 Normal Hamster Price Alert!\n"
        f"Price: ${price:.2f}\n"
        f"Threshold: ${THRESHOLD:.2f}\n"
        f"Time: {ts}"
    )
    send_discord(msg)
    save_last_alert(datetime.utcnow())

driver.quit()
