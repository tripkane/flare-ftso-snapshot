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

# Helper to extract integer sequences
def extract_numbers(text):
    return re.findall(r"\d[\d,]*", text)

# Helper to extract decimal numbers
def extract_decimal(text):
    m = re.search(r"\d+\.\d+", text)
    return m.group(0) if m else re.sub(r"[^0-9.]", "", text)

# Scrape flaremetrics.io main Flare network stats
def scrape_flaremetrics(driver):
    """Scrape flaremetrics.io Flare network stats using BeautifulSoup."""
    url = "https://flaremetrics.io/flare"
    driver.get(url)
    time.sleep(5)  # wait for JS
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    providers = []
    # Iterate table rows
    for row in soup.select("table tbody tr"):
        cols = row.find_all("td")
        if len(cols) < 7:
            continue
        rank = cols[0].get_text(strip=True)
        name = cols[1].get_text(strip=True)
        # Vote power extraction via spans
        vote_cell = cols[2]
        spans = vote_cell.find_all('span')
        if len(spans) >= 2:
            vote_power = spans[0].get_text(strip=True)
            vote_power_locked = spans[1].get_text(strip=True)
        else:
            text = vote_cell.get_text(strip=True)
            nums = extract_numbers(text)
            vote_power = nums[0] if nums else ''
            vote_power_locked = nums[1] if len(nums) > 1 else ''
        # Percentages and other cells
        vote_power_pct = cols[3].get_text(strip=True)
        vote_power_pct_locked = ''
        pct_spans = cols[3].find_all('span')
        if len(pct_spans) >= 2:
            vote_power_pct = pct_spans[0].get_text(strip=True)
            vote_power_pct_locked = pct_spans[1].get_text(strip=True)
        change_24h_pct = cols[4].get_text(strip=True)
        reward_cell = cols[5]
        # reward rate may include span for tooltip
        reward_spans = reward_cell.find_all('span')
        if reward_spans:
            reward_rate = reward_spans[0].get_text(strip=True)
        else:
            reward_rate = reward_cell.get_text(strip=True)
        registered = cols[6].get_text(strip=True)
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
