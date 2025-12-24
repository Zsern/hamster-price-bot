import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests

# ===================== CONFIG =====================
STAR_PETS_URL = "https://starpets.gg/adopt-me/shop/pet/hamster/24098"
THRESHOLD = 0.26
ALERT_COOLDOWN = timedelta(hours=3)

# Discord webhook from GitHub Secrets
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
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
        if response.status_code >= 400:
            print(f"[WARN] Discord webhook returned {response.status_code}: {response.text}")
    except Exception as e:
        print("[WARN] Discord send failed:", e)

# ===================== SCRAPER =====================
def get_lowest_normal_price():
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(STAR_PETS_URL, headers=headers, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print("[ERROR] Failed to fetch page:", e)
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    container = soup.find("div", class_="_content_top_right_2ox1k_243")
    if not container:
        print("[WARN] Container missing.")
        return None

    price_span = container.find("span", itemprop="price")
    if not price_span:
        print("[WARN] Price span missing.")
        return None

    price_str = price_span.get("content", "")
    if not price_str:
        print("[WARN] Price content missing:", price_span)
        return None

    try:
        return float(price_str)
    except Exception as e:
        print("[ERROR] Failed to convert price to float:", price_str, e)
        return None

# ===================== MAIN =====================
def main():
    print("[INFO] Normal Hamster Price Alert Bot started!")

    try:
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
    except Exception as e:
        print("[ERROR] Script failed:", e)

if _name_ == "_main_":
    main()
