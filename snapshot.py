import json
import datetime
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from selenium.webdriver.chrome.service import Service

def init_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = "/usr/bin/chromium-browser"

    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

def scrape_flaremetrics(driver):
    driver.get("https://flaremetrics.io/songbird")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    providers = []
    for row in soup.select("table tbody tr"):
        cols = row.find_all("td")
        if len(cols) >= 3:
            providers.append({
                "provider": cols[0].get_text(strip=True),
                "vote_power": cols[1].get_text(strip=True),
                "reward_rate": cols[2].get_text(strip=True)
            })
    return providers

def scrape_flare_systems(driver):
    driver.get("https://flare-systems-explorer.flare.network/providers?tab=fsp&asc=false&sortBy=display_name")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    providers = []
    for row in soup.select("table tbody tr"):
        cols = row.find_all("td")
        if len(cols) >= 2:
            providers.append({
                "provider": cols[0].get_text(strip=True),
                "score": cols[1].get_text(strip=True)
            })
    return providers

def main():
    today = datetime.date.today().isoformat()
    outfile = f"ftso_snapshot_{today}.json"
    snapshot = {"date": today, "flaremetrics": [], "flare_systems_explorer": []}

    driver = init_driver()
    try:
        snapshot["flaremetrics"] = scrape_flaremetrics(driver)
        snapshot["flare_systems_explorer"] = scrape_flare_systems(driver)
    finally:
        driver.quit()

    os.makedirs("daily_snapshots", exist_ok=True)
    with open(f"daily_snapshots/{outfile}", "w") as f:
        json.dump(snapshot, f, indent=2)

    print(f"[SUCCESS] Snapshot saved to daily_snapshots/{outfile}")

if __name__ == '__main__':
    main()
