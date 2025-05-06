import json
import datetime
import os
import time
import re
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

# Initialize headless browser
def init_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = "/usr/bin/chromium-browser"
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

# Helpers for extracting numbers and decimals

def extract_numbers(text):
    """Extract integer sequences from text, preserving commas."""
    return re.findall(r"\d[\d,]*", text)

def extract_decimal(text):
    """Extract a floating-point number from text."""
    m = re.search(r"\d+\.\d+", text)  # Match valid decimal numbers
    if m:
        return m.group(0)
    # Fallback: remove non-digit and non-dot characters
    cleaned = re.sub(r"[^0-9.]", "", text)
    # Ensure the cleaned value is a valid float
    if cleaned.count('.') > 1 or cleaned == '.':  # Invalid if multiple dots or just a dot
        return None
    return cleaned

# Scrape flaremetrics.io (Flare or Songbird network)
def scrape_flaremetrics(driver, network="flare"):
    if network == "flare":
        url = "https://flaremetrics.io/"
    elif network == "songbird":
        url = "https://flaremetrics.io/songbird"
    else:
        raise ValueError("Unknown network: " + network)
    driver.get(url)
    time.sleep(5)  # allow JS to render table
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    providers = []
    # Table columns: rank, Name, Vote Power, Vote Power %, 24h %, Reward Rate, Registered
    for row in soup.select("table tbody tr"):
        cols = row.find_all("td")
        if len(cols) >= 7:
            rank = cols[0].get_text(strip=True)
            name = cols[1].get_text(strip=True)
            raw_vote = cols[2].get_text("", strip=True)
            raw_vote_pct = cols[3].get_text("", strip=True)
            raw_change_24h = cols[4].get_text("", strip=True)
            raw_reward = cols[5].get_text("", strip=True)
            registered = cols[6].get_text(strip=True)

            # --- Updated vote_power/vote_power_locked logic ---
            vote_nums = extract_numbers(raw_vote)
            if len(vote_nums) >= 2:
                # Already split, just clean commas and convert to int
                vote_power = int(vote_nums[0].replace(",", "")) if vote_nums[0] else 0
                vote_power_locked = int(vote_nums[1].replace(",", "")) if vote_nums[1] else 0
            elif len(vote_nums) == 1:
                # Only one number, use for both
                num = vote_nums[0].replace(",", "")
                vote_power = int(num) if num else 0
                vote_power_locked = int(num) if num else 0
            else:
                # Fallback: try to split the raw_vote string in half (legacy case)
                vp = raw_vote.replace(",", "")
                if vp and len(vp) % 2 == 0:
                    mid = len(vp) // 2
                    vp1 = vp[:mid]
                    vp2 = vp[mid:]
                    vote_power = int(vp1) if vp1.isdigit() else 0
                    vote_power_locked = int(vp2) if vp2.isdigit() else 0
                else:
                    vote_power = 0
                    vote_power_locked = 0

            # Extract vote power percentages
            pcts = re.findall(r"[0-9][0-9.,]*%", raw_vote_pct)
            vote_power_pct = float(pcts[0].replace('%', '').replace(',', '')) if len(pcts) > 0 else 0.0
            vote_power_pct_locked = float(pcts[1].replace('%', '').replace(',', '')) if len(pcts) > 1 else 0.0

            # 24h change percent
            change_pcts = re.findall(r"[0-9][0-9.,]*%", raw_change_24h)
            change_24h_pct = float(change_pcts[0].replace('%', '').replace(',', '')) if change_pcts else 0.0

            # Reward rate as decimal
            reward_rate = float(extract_decimal(raw_reward)) if extract_decimal(raw_reward) else 0.0

            providers.append({
                "rank": rank,
                "name": name,
                "vote_power": vote_power,
                "vote_power_locked": vote_power_locked,
                "vote_power_pct": vote_power_pct,
                "vote_power_pct_locked": vote_power_pct_locked,
                "change_24h_pct": change_24h_pct,
                "reward_rate": reward_rate,
                "registered": registered
            })
    return providers

# Save snapshot to JSON
def save_snapshot(data, network="flare"):
    today = datetime.date.today().isoformat()
    os.makedirs("daily_snapshots", exist_ok=True)
    filename = f"daily_snapshots/{network}_snapshot_{today}.json"
    with open(filename, 'w') as f:
        json.dump({"date": today, "providers": data}, f, indent=2)
    print(f"Snapshot saved: {filename}")

# Main entrypoint
def main(network="flare"):
    driver = init_driver()
    try:
        current_data = scrape_flaremetrics(driver, network)
    finally:
        driver.quit()

    save_snapshot(current_data, network)

if __name__ == '__main__':
    # Usage: python snapshot.py [flare|songbird]
    networks = ["flare", "songbird"]
    if len(sys.argv) > 1 and sys.argv[1] in networks:
        main(sys.argv[1])
    else:
        for net in networks:
            main(net)