import json
import datetime
import os
import time
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

# Scrape flaremetrics.io for detailed stats
def scrape_flaremetrics(driver):
    url = "https://flaremetrics.io/"
    driver.get(url)
    time.sleep(5)  # allow JS to render table
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    providers = []
    rows = soup.select("table tbody tr")
    for row in rows:
        cols = row.find_all("td")
        # Expecting 7 columns: rank, name, vote power, vote power %, 24h %, reward rate, registered
        if len(cols) >= 7:
            providers.append({
                "rank": cols[0].get_text(strip=True),
                "name": cols[1].get_text(strip=True),
                "vote_power": cols[2].get_text(strip=True),
                "vote_power_pct": cols[3].get_text(strip=True),
                "change_24h_pct": cols[4].get_text(strip=True),
                "reward_rate": cols[5].get_text(strip=True),
                "registered": cols[6].get_text(strip=True)
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
