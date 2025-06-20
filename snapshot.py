import json
import datetime
import os
import re
import sys
from typing import List, Dict

from flare_rpc import connect, list_providers

MAX_RETRIES = int(os.getenv("SNAPSHOT_RETRIES", "6"))
RETRY_DELAY = int(os.getenv("SNAPSHOT_RETRY_DELAY", "600"))  # seconds

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
def fetch_chain_data(network: str = "flare") -> List[Dict[str, str]]:
    """Return basic provider data directly from the blockchain."""
    w3 = connect()
    addresses = list_providers(w3)
    return [{"address": addr} for addr in addresses]

# Save snapshot to JSON
def save_snapshot(data, network="flare"):
    today = datetime.date.today().isoformat()
    subdir = today[:7]
    out_dir = os.path.join("daily_snapshots", subdir)
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{network}_snapshot_{today}.json"
    path = os.path.join(out_dir, filename)
    if os.path.exists(path):
        print(f"Snapshot already exists: {path}")
    else:
        with open(path, "w") as f:
            json.dump({"date": today, "providers": data}, f, indent=2)
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
def main(network="flare"):
    schedule = load_epoch_schedule()
    if not is_current_time_epoch_start(schedule):
        now = datetime.datetime.utcnow().isoformat(timespec="minutes")
        print(f"{now} is not an epoch start. Exiting.")
        return

    current_data = fetch_chain_data(network)

    save_snapshot(current_data, network)

    clean_snapshots(schedule, network=network)

if __name__ == '__main__':
    # Usage: python snapshot.py [flare|songbird]
    networks = ["flare", "songbird"]
    if len(sys.argv) > 1 and sys.argv[1] in networks:
        main(sys.argv[1])
    else:
        for net in networks:
            main(net)
