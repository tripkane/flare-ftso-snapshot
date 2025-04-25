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
    m = re.search(r"\d+\.\d+", text)  # Match valid decimal numbers
    if m:
        return m.group(0)
    # Fallback: remove non-digit and non-dot characters
    cleaned = re.sub(r"[^0-9.]", "", text)
    # Ensure the cleaned value is a valid float
    if cleaned.count('.') > 1 or cleaned == '.':  # Invalid if multiple dots or just a dot
        return None
    return cleaned

# Scrape flaremetrics.io (Songbird network)
def scrape_flaremetrics(driver):
    url = "https://flaremetrics.io/"
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
                    vote_power = vote_nums[0] if vote_nums else '0'
                    vote_power_locked = '0'

            # Extract vote power percentages
            pcts = re.findall(r"[0-9][0-9.,]*%", raw_vote_pct)
            vote_power_pct = float(pcts[0].replace('%', '').replace(',', '')) if len(pcts) > 0 else 0.0
            vote_power_pct_locked = float(pcts[1].replace('%', '').replace(',', '')) if len(pcts) > 1 else 0.0

            # 24h change percent
            change_pcts = re.findall(r"[0-9][0-9.,]*%", raw_change_24h)
            change_24h_pct = float(change_pcts[0].replace('%', '').replace(',', '')) if change_pcts else 0.0

            # Reward rate as decimal
            reward_rate = float(extract_decimal(raw_reward)) if extract_decimal(raw_reward) else 0.0

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

def load_previous_snapshot():
    """Load the most recent snapshot from the daily_snapshots directory."""
    snapshots_dir = "daily_snapshots"
    files = sorted(
        [f for f in os.listdir(snapshots_dir) if f.endswith(".json")],
        reverse=True
    )
    if len(files) < 2:
        return None  # No previous snapshot available
    with open(os.path.join(snapshots_dir, files[1]), 'r') as f:
        return json.load(f)

def compare_snapshots(current, previous):
    """Compare the current snapshot with the previous one."""
    previous_providers = {p["name"]: p for p in previous.get("providers", [])}
    report = []

    for provider in current.get("providers", []):
        name = provider["name"]
        current_reward_rate = provider["reward_rate"]
        current_registered = provider["registered"]

        if name in previous_providers:
            previous_reward_rate = previous_providers[name]["reward_rate"]
            previous_registered = previous_providers[name]["registered"]

            # Check if reward rate changed to NaN
            if not current_reward_rate and previous_reward_rate > 0:
                report.append({
                    "name": name,
                    "previous_reward_rate": previous_reward_rate,
                    "current_reward_rate": current_reward_rate,
                    "current_registered": current_registered
                })

    return report

def save_report(report):
    """Save the report to a JSON file."""
    today = datetime.date.today().isoformat()
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/reward_rate_changes_{today}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Report saved: {filename}")

# Main entrypoint
def main():
    driver = init_driver()
    try:
        current_data = scrape_flaremetrics(driver)
    finally:
        driver.quit()

    save_snapshot(current_data)

    # Load the previous snapshot and compare
    previous_data = load_previous_snapshot()
    if previous_data:
        report = compare_snapshots({"providers": current_data}, previous_data)
        save_report(report)

if __name__ == '__main__':
    main()
