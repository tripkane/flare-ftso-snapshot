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

# Scrape flaremetrics.io (Songbird network)
def scrape_flaremetrics(driver):
    url = "https://flaremetrics.io/songbird"
    driver.get(url)
    time.sleep(5)  # allow JS to render table
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    providers = []
    # Table columns: # (rank), Name, Vote Power, Vote Power %, 24h %, Reward Rate, Registered
    for row in soup.select("table tbody tr"):
        cols = row.find_all("td")
        if len(cols) >= 7:
            rank = cols[0].get_text(strip=True)
            name = cols[1].get_text(strip=True)
            raw_vote = cols[2].get_text(strip=True)
            raw_vote_pct = cols[3].get_text(strip=True)
            raw_change_24h = cols[4].get_text(strip=True)
            raw_reward = cols[5].get_text(strip=True)
            registered = cols[6].get_text(strip=True)
            # Clean numeric values
            vote_power = re.sub(r"[^0-9.,]", "", raw_vote)
            vote_power_pct = re.sub(r"[^0-9.,%-]", "", raw_vote_pct)
            change_24h = re.sub(r"[^0-9.,%-]", "", raw_change_24h)
            reward_rate = re.sub(r"[^0-9.,]", "", raw_reward)
            providers.append({
                "rank": rank,
                "name": name,
                "vote_power": vote_power,
                "vote_power_pct": vote_power_pct,
                "change_24h_pct": change_24h,
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
