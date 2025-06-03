import os
import json
import datetime

def load_epoch_schedule(file_path="flare_epoch_schedule.json"):
    """Load the epoch schedule from a JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading epoch schedule: {e}")
        return []

def is_snapshot_relevant(snapshot_date, schedule):
    """Check if a snapshot date falls within any epoch in the schedule."""
    snapshot_datetime = datetime.datetime.strptime(snapshot_date, "%Y-%m-%d")
    for epoch in schedule:
        start = datetime.datetime.strptime(epoch["Start (UTC)"], "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(epoch["End (UTC)"], "%Y-%m-%d %H:%M:%S")
        if start.date() <= snapshot_datetime.date() <= end.date():
            return True
    return False

def clean_snapshots(schedule, snapshot_dir="daily_snapshots"):
    """Delete snapshots that aren't relevant based on the epoch schedule."""
    if not os.path.exists(snapshot_dir):
        print(f"Snapshot directory '{snapshot_dir}' does not exist.")
        return

    for filename in os.listdir(snapshot_dir):
        if filename.endswith(".json"):
            snapshot_date = filename.split("_")[-1].replace(".json", "")
            try:
                if not is_snapshot_relevant(snapshot_date, schedule):
                    file_path = os.path.join(snapshot_dir, filename)
                    os.remove(file_path)
                    print(f"Deleted irrelevant snapshot: {file_path}")
            except Exception as e:
                print(f"Error processing file '{filename}': {e}")

if __name__ == "__main__":
    # Load epoch schedule
    schedule = load_epoch_schedule()

    # Clean snapshots
    clean_snapshots(schedule)