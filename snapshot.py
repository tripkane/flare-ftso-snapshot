from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
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

# Scrape Minimal Conditions tab
def scrape_minimal_conditions(driver):
    url = "https://flare-systems-explorer.flare.network/providers?tab=minimalConditions"
    driver.get(url)
    time.sleep(10)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    rows = soup.select("table tbody tr")
    data = {}
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 7:
            name = cols[0].get_text(strip=True)
            data[name] = {
                "ftso_anchor_feeds": cols[1].get_text(strip=True),
                "ftso_latency_feeds": cols[2].get_text(strip=True),
                "fdc": cols[3].get_text(strip=True),
                "staking": cols[4].get_text(strip=True),
                "passes": cols[5].get_text(strip=True),
                "eligible_for_reward": cols[6].get_text(strip=True)
            }
    return data

# Scrape FSP tab
def scrape_fsp_tab(driver):
    url = "https://flare-systems-explorer.flare.network/providers?tab=fsp&asc=false&sortBy=display_name"
    driver.get(url)
    time.sleep(10)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    rows = soup.select("table tbody tr")
    data = {}
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 14:
            name = cols[0].get_text(strip=True)
            data[name] = {
                "fsp_participating": cols[1].get_text(strip=True),
                "direct_earnings": cols[2].get_text(strip=True),
                "fee_rewards": cols[3].get_text(strip=True),
                "delegation_rewards": cols[4].get_text(strip=True),
                "delegation_reward_rate": cols[5].get_text(strip=True),
                "delegation_weight": cols[6].get_text(strip=True),
                "delegation_rate": cols[7].get_text(strip=True),
                "staking_rewards": cols[8].get_text(strip=True),
                "staking_reward_rate": cols[9].get_text(strip=True),
                "staking_weight": cols[10].get_text(strip=True),
                "fee": cols[11].get_text(strip=True),
                "uptime_signed": cols[12].get_text(strip=True),
                "rewards_signed": cols[13].get_text(strip=True)
            }
    return data

# Scrape FTSO tab
def scrape_ftso_tab(driver):
    url = "https://flare-systems-explorer.flare.network/providers?tab=ftso&asc=false&sortBy=display_name"
    driver.get(url)
    time.sleep(10)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    rows = soup.select("table tbody tr")
    data = {}
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
            name = cols[0].get_text(strip=True)
            data[name] = {
                "ftso_participating": cols[1].get_text(strip=True),
                "primary": cols[2].get_text(strip=True),
                "secondary": cols[3].get_text(strip=True),
                "availability": cols[4].get_text(strip=True)
            }
    return data

# Merge all scraped data
def merge_provider_data(*dicts):
    merged = {}
    for data in dicts:
        for name, values in data.items():
            if name not in merged:
                merged[name] = {"name": name}
            merged[name].update(values)
    return list(merged.values())

# Save snapshot JSON
def save_snapshot(data):
    today = datetime.date.today().isoformat()
    filename = f"daily_snapshots/ftso_snapshot_{today}.json"
    os.makedirs("daily_snapshots", exist_ok=True)
    with open(filename, "w") as f:
        json.dump({"date": today, "providers": data}, f, indent=2)
    print(f"Snapshot saved: {filename}")

# Main flow
def main():
    driver = init_driver()
    try:
        minimal_data = scrape_minimal_conditions(driver)
        fsp_data = scrape_fsp_tab(driver)
        ftso_data = scrape_ftso_tab(driver)
        all_data = merge_provider_data(minimal_data, fsp_data, ftso_data)
        save_snapshot(all_data)
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
