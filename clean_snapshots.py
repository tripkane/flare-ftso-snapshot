import os
import json
import datetime
import re
"""test comment"""
def load_epoch_schedule(file_path="flare_epoch_schedule.json"):
    """Load the epoch schedule from a JSON file and extract only the start dates."""
    try:
        with open(file_path, "r") as f:
            schedule = json.load(f)
        # Extract only the start dates as datetime.date objects
        start_dates = [
            datetime.datetime.strptime(epoch["Start (UTC)"], "%Y-%m-%d %H:%M:%S").date()
            for epoch in schedule
        ]
        return start_dates
    except Exception as e:
        print(f"Error loading epoch schedule: {e}")
        return []

def is_snapshot_relevant(snapshot_date, start_dates):
    """Check if a snapshot date matches any start date in the schedule."""
    snapshot_date = datetime.datetime.strptime(snapshot_date, "%Y-%m-%d").date()
    return snapshot_date in start_dates

def clean_snapshots(
    start_dates,
    snapshot_dir="daily_snapshots",
    docs_dir=None,
    manifest_path=None,
    network=None,
):
    """Delete irrelevant snapshots and update docs/manifest."""
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

    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    for root, _, files in os.walk(snapshot_dir):
        for filename in files:
            if filename == "manifest.json":
                continue
            if not filename.endswith(".json"):
                continue
            if not date_pattern.search(filename):
                continue
            rel_path = os.path.relpath(os.path.join(root, filename), snapshot_dir)
            snapshot_date = filename.split("_")[-1].replace(".json", "")
            try:
                if not is_snapshot_relevant(snapshot_date, start_dates):
                    file_path = os.path.join(root, filename)
                    os.remove(file_path)
                    print(f"Deleted irrelevant snapshot: {file_path}")

                    doc_file = os.path.join(docs_dir, rel_path)
                    if os.path.exists(doc_file):
                        os.remove(doc_file)

                    if network and rel_path in manifest.get(network, []):
                        manifest[network].remove(rel_path)
                else:
                    print(f"Snapshot is relevant: {filename}")
            except Exception as e:
                print(f"Error processing file '{filename}': {e}")

    if network:
        manifest[network] = [
            f
            for f in manifest.get(network, [])
            if os.path.exists(os.path.join(docs_dir, f))
        ]

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    import sys

    # allow optional directory argument
    snapshot_dir = sys.argv[1] if len(sys.argv) > 1 else "daily_snapshots"

    # Load epoch start dates
    start_dates = load_epoch_schedule()

    # Clean snapshots
    clean_snapshots(start_dates, snapshot_dir=snapshot_dir)
