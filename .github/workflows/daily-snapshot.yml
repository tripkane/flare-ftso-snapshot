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

# Scrape flaremetrics.io

def scrape_flaremetrics(driver):
    url = "https://flaremetrics.io/songbird"
    driver.get(url)
    time.sleep(5)  # wait for data to load
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    providers = []
    for row in soup.select("table tbody tr"):
        cols = row.find_all("td")
        if len(cols) >= 3:
            providers.append({
                "name": cols[0].get_text(strip=True),
                "vote_power": cols[1].get_text(strip=True),
                "reward_rate": cols[2].get_text(strip=True)
            })
    return providers

# Save snapshot

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
