import json
import datetime
import os
import time
import re
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

MAX_RETRIES = int(os.getenv("SNAPSHOT_RETRIES", "6"))
RETRY_DELAY = int(os.getenv("SNAPSHOT_RETRY_DELAY", "600"))  # seconds

# Initialize headless browser
def init_driver():
    """Initialise a headless Chrome driver.

    Paths to the Chromium binary and chromedriver can be overridden with the
    ``CHROMIUM_BINARY`` and ``CHROMEDRIVER`` environment variables
    respectively. This allows the scraper to run in environments where the
    browser is installed in a non-standard location.
    """

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    binary_path = os.getenv('CHROMIUM_BINARY', '/usr/bin/chromium-browser')
    driver_path = os.getenv('CHROMEDRIVER', '/usr/bin/chromedriver')
    options.binary_location = binary_path
    service = Service(driver_path)
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

# Scrape flaremetrics.io (Flare or Songbird network)
def scrape_flaremetrics(driver, network="flare"):
    if network == "flare":
        url = "https://flaremetrics.io/"
    elif network == "songbird":
        url = "https://flaremetrics.io/songbird"
    else:
        raise ValueError("Unknown network: " + network)
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

            # --- Updated vote_power/vote_power_locked logic ---
            vote_nums = extract_numbers(raw_vote)
            if len(vote_nums) >= 2:
                # Already split, just clean commas and convert to int
                vote_power = int(vote_nums[0].replace(",", "")) if vote_nums[0] else 0
                vote_power_locked = int(vote_nums[1].replace(",", "")) if vote_nums[1] else 0
            elif len(vote_nums) == 1:
                # Single number present. Check for doubled value pattern.
                num = vote_nums[0].replace(",", "")
                if num and len(num) % 2 == 0:
                    half = len(num) // 2
                    first, second = num[:half], num[half:]
                    if first == second:
                        vote_power = int(first)
                        vote_power_locked = int(second)
                    else:
                        vote_power = int(num)
                        vote_power_locked = int(num)
                else:
                    vote_power = int(num) if num else 0
                    vote_power_locked = int(num) if num else 0
            else:
                # Fallback: try to split the raw_vote string in half (legacy case)
                vp = raw_vote.replace(",", "")
                if vp and len(vp) % 2 == 0:
                    mid = len(vp) // 2
                    vp1 = vp[:mid]
                    vp2 = vp[mid:]
                    vote_power = int(vp1) if vp1.isdigit() else 0
                    vote_power_locked = int(vp2) if vp2.isdigit() else 0
                else:
                    vote_power = 0
                    vote_power_locked = 0

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

def scrape_with_retries(network="flare", max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Scrape flaremetrics with retry logic."""
    attempt = 0
    while attempt < max_retries:
        driver = init_driver()
        try:
            data = scrape_flaremetrics(driver, network)
            if data:
                return data
            else:
                print(f"No data retrieved for {network} on attempt {attempt + 1}")
        except Exception as e:
            print(f"Error scraping {network} on attempt {attempt + 1}: {e}")
        finally:
            driver.quit()
        attempt += 1
        if attempt < max_retries:
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    print(f"Failed to scrape data for {network} after {max_retries} attempts")
    return []

# Save snapshot to JSON
def save_snapshot(data, network="flare", snapshot_date=None):
    """Save provider data to ``daily_snapshots`` and docs.

    Parameters
    ----------
    data : list
        Provider records returned by the scraper.
    network : str, optional
        Either ``"flare"`` or ``"songbird"``. Defaults to ``"flare"``.
    snapshot_date : str, optional
        ISO formatted date string (``YYYY-MM-DD``) to use for the file name.
        When ``None`` the current UTC date is used.
    """

    if snapshot_date is None:
        snapshot_date = datetime.date.today().isoformat()
    subdir = snapshot_date[:7]
    out_dir = os.path.join("daily_snapshots", subdir)
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{network}_snapshot_{snapshot_date}.json"
    path = os.path.join(out_dir, filename)
    if os.path.exists(path):
        print(f"Snapshot already exists: {path}")
    else:
        with open(path, "w") as f:
            json.dump({"date": snapshot_date, "providers": data}, f, indent=2)
        print(f"Snapshot saved: {path}")

    copy_snapshot_to_docs(path, network)


def copy_snapshot_to_docs(path, network):
    """Copy snapshot to docs directory and update manifest."""
    docs_dir = os.path.join("docs", "daily_snapshots")
    rel_path = os.path.relpath(path, "daily_snapshots")
    dest = os.path.join(docs_dir, rel_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(path) as src, open(dest, "w") as dst:
        dst.write(src.read())
    update_docs_manifest(docs_dir, rel_path, network)


def snapshot_exists(snapshot_date, network):
    """Return True if a snapshot file already exists for ``snapshot_date``."""
    subdir = snapshot_date[:7]
    filename = f"{network}_snapshot_{snapshot_date}.json"
    path = os.path.join("daily_snapshots", subdir, filename)
    return os.path.exists(path)


def update_docs_manifest(docs_dir, filename, network):
    manifest_path = os.path.join(docs_dir, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        manifest = {"flare": [], "songbird": []}
    manifest.setdefault(network, [])

    if filename not in manifest[network]:
        manifest[network].append(filename)

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def check_for_missing_snapshots(schedule, network="flare"):
    """Capture snapshots for any past epoch start dates with missing files."""
    today = datetime.date.today()
    for epoch in schedule:
        start_dt = datetime.datetime.strptime(epoch["Start (UTC)"], "%Y-%m-%d %H:%M:%S")
        if start_dt.date() > today:
            break
        date_str = start_dt.date().isoformat()
        if not snapshot_exists(date_str, network):
            print(f"Missing snapshot for {network} on {date_str}. Capturing now...")
            data = scrape_with_retries(network)
            save_snapshot(data, network=network, snapshot_date=date_str)

def load_epoch_schedule(file_path="flare_epoch_schedule.json"):
    """Load the epoch schedule from a JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading epoch schedule: {e}")
        return []

def is_snapshot_relevant(snapshot_date, schedule):
    """Return True if snapshot_date exactly matches an epoch start date."""
    snapshot_day = datetime.datetime.strptime(snapshot_date, "%Y-%m-%d").date()
    for epoch in schedule:
        start = datetime.datetime.strptime(epoch["Start (UTC)"], "%Y-%m-%d %H:%M:%S").date()
        if snapshot_day == start:
            return True
    return False

def is_current_time_epoch_start(schedule, now=None):
    """Return True if ``now`` matches an epoch start timestamp."""
    if now is None:
        now = datetime.datetime.utcnow().replace(second=0, microsecond=0)
    for epoch in schedule:
        start = datetime.datetime.strptime(epoch["Start (UTC)"], "%Y-%m-%d %H:%M:%S")
        if now == start:
            return True
    return False

def clean_snapshots(
    schedule,
    snapshot_dir="daily_snapshots",
    docs_dir=None,
    manifest_path=None,
    network=None,
):
    """Delete snapshots that aren't relevant and update docs/manifest."""
    if not os.path.exists(snapshot_dir):
        print(f"Snapshot directory '{snapshot_dir}' does not exist.")
        return

    if docs_dir is None:
        docs_dir = os.path.join("docs", "daily_snapshots")
    if manifest_path is None:
        manifest_path = os.path.join(docs_dir, "manifest.json")

    manifest = {"flare": [], "songbird": []}
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except Exception:
            pass

    for root, _, files in os.walk(snapshot_dir):
        for filename in files:
            if not filename.endswith(".json"):
                continue
            rel_path = os.path.relpath(os.path.join(root, filename), snapshot_dir)
            snapshot_date = filename.split("_")[-1].replace(".json", "")
            try:
                if not is_snapshot_relevant(snapshot_date, schedule):
                    file_path = os.path.join(root, filename)
                    os.remove(file_path)
                    print(f"Deleted irrelevant snapshot: {file_path}")

                    doc_file = os.path.join(docs_dir, rel_path)
                    if os.path.exists(doc_file):
                        os.remove(doc_file)

                    if network and rel_path in manifest.get(network, []):
                        manifest[network].remove(rel_path)
            except Exception as e:
                print(f"Error processing file '{filename}': {e}")

    # Finalize manifest: remove entries with missing files
    if network:
        manifest[network] = [
            f
            for f in manifest.get(network, [])
            if os.path.exists(os.path.join(docs_dir, f))
        ]

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

# Main entrypoint
def main(network="flare", force=False):
    schedule = load_epoch_schedule()

    if force or is_current_time_epoch_start(schedule):
        current_data = scrape_with_retries(network)
        save_snapshot(current_data, network)
    else:
        now = datetime.datetime.utcnow().isoformat(timespec="minutes")
        print(f"{now} is not an epoch start. Skipping live snapshot.")

    check_for_missing_snapshots(schedule, network)
    clean_snapshots(schedule, network=network)

if __name__ == '__main__':
    # Usage: python snapshot.py [flare|songbird] [--force|-f]
    networks = ["flare", "songbird"]
    force = False
    selected = []
    for arg in sys.argv[1:]:
        if arg in ("--force", "-f"):
            force = True
        elif arg in networks:
            selected.append(arg)

    if not selected:
        selected = networks

    for net in selected:
        main(net, force=force)
