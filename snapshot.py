from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import os
import datetime

# Initialize headless browser
def init_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = "/usr/bin/chromium-browser"
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

def scrape_table(driver, url, expected_columns):
    print(f"Scraping: {url}")
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    rows = soup.select("table tbody tr")
    print(f"Found {len(rows)} rows")
    data = {}
    for i, row in enumerate(rows):
        cols = row.find_all("td")
        print(f"Row {i+1}: {len(cols)} columns")
        if cols:
            name = cols[0].get_text(strip=True)
            print(f" → First column text: {name}")
            if name and len(cols) >= len(expected_columns):
                data[name] = {expected_columns[i]: cols[i].get_text(strip=True) for i in range(1, len(expected_columns))}
    print(f"Scraped {len(data)} providers from this table")
    return data

def scrape_all_tabs(driver):
    minimal_cols = ["provider", "ftso_anchor_feeds", "ftso_latency_feeds", "fdc", "staking", "passes", "eligible_for_reward"]
    fsp_cols = ["provider", "fsp_participating", "direct_earnings", "fee_rewards", "delegation_rewards", "delegation_reward_rate", "delegation_weight", "delegation_rate", "staking_rewards", "staking_reward_rate", "staking_weight", "fee", "uptime_signed", "rewards_signed"]
    ftso_cols = ["provider", "ftso_participating", "primary", "secondary", "availability"]

    urls = {
        "minimal": ("https://flare-systems-explorer.flare.network/providers?tab=minimalConditions", minimal_cols),
        "fsp": ("https://flare-systems-explorer.flare.network/providers?tab=fsp&asc=false&sortBy=display_name", fsp_cols),
        "ftso": ("https://flare-systems-explorer.flare.network/providers?tab=ftso&asc=false&sortBy=display_name", ftso_cols),
    }

    all_data = {}
    for label, (url, columns) in urls.items():
        tab_data = scrape_table(driver, url, columns)
        for name, values in tab_data.items():
            if name not in all_data:
                all_data[name] = {"name": name}
            all_data[name].update(values)

    return list(all_data.values())

def save_snapshot(data):
    today = datetime.date.today().isoformat()
    filename = f"daily_snapshots/ftso_snapshot_{today}.json"
    os.makedirs("daily_snapshots", exist_ok=True)
    with open(filename, "w") as f:
        json.dump({"date": today, "providers": data}, f, indent=2)
    print(f"Snapshot saved: {filename}")

def main():
    driver = init_driver()
    try:
        data = scrape_all_tabs(driver)
        save_snapshot(data)
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
