import json
import datetime
import os
import time
import re
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
    m = re.search(r"\d+\.\d+", text)
    if m:
        return m.group(0)
    # Fallback: remove non-digit and non-dot characters
    cleaned = re.sub(r"[^0-9.]", "", text)
    return cleaned

# Scrape flaremetrics.io (Songbird network)
def scrape_flaremetrics(driver):
    url = "https://flaremetrics.io"
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

            # Extract vote power and locked vote power
            vote_nums = extract_numbers(raw_vote)
            if len(vote_nums) >= 2:
                vote_power = vote_nums[0]
                vote_power_locked = vote_nums[1]
            else:
                m = re.match(r"^([0-9,]+?)\1$", raw_vote)
                if m:
                    vote_power = m.group(1)
                    vote_power_locked = m.group(1)
                else:
                    vote_power = vote_nums[0] if vote_nums else ''
                    vote_power_locked = ''

            # Extract vote power percentages
            pcts = re.findall(r"[0-9][0-9.,]*%", raw_vote_pct)
            vote_power_pct = pcts[0] if len(pcts) > 0 else ''
            vote_power_pct_locked = pcts[1] if len(pcts) > 1 else ''

            # 24h change percent
            change_pcts = re.findall(r"[0-9][0-9.,]*%", raw_change_24h)
            change_24h_pct = change_pcts[0] if change_pcts else ''

            # Reward rate as decimal
            reward_rate = extract_decimal(raw_reward)

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
def save_snapshot(data):
    today = datetime.date.today().isoformat()
    os.makedirs("daily_snapshots", exist_ok=True)
    filename = f"daily_snapshots/ftso_snapshot_{today}.json"
    with open(filename, 'w') as f:
        json.dump({"date": today, "providers": data}, f, indent=2)
    print(f"Snapshot saved: {filename}")

# Main entrypoint
def main():
    driver = init_driver()
    try:
        data = scrape_flaremetrics(driver)
    finally:
        driver.quit()
    save_snapshot(data)

if __name__ == '__main__':
    main()
