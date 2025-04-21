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
    for row in soup.select("table tbody tr"):
        cols = row.find_all("td")
        # Expecting: rank, name, vote power, reward rate, ...
        if len(cols) >= 4:
            name = cols[1].get_text(strip=True)
            raw_vote = cols[2].get_text(strip=True)
            raw_reward = cols[3].get_text(strip=True)
            # Clean numeric values (remove non-digits except . and ,)
            vote_power = re.sub(r"[^0-9.,]", "", raw_vote)
            reward_rate = re.sub(r"[^0-9.,]", "", raw_reward)
            providers.append({
                "name": name,
                "vote_power": vote_power,
                "reward_rate": reward_rate
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
