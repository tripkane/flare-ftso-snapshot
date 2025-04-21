from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    data = {}
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) >= len(expected_columns):
            name = cols[0].text.strip()
            if name:
                data[name] = {expected_columns[i]: cols[i].text.strip() for i in range(1, len(expected_columns))}
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
