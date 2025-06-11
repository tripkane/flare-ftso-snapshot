import os
import json
import datetime

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

def clean_snapshots(start_dates, snapshot_dir="daily_snapshots"):
    """Delete snapshots that aren't relevant based on the epoch start dates."""
    if not os.path.exists(snapshot_dir):
        print(f"Snapshot directory '{snapshot_dir}' does not exist.")
        return

    for filename in os.listdir(snapshot_dir):
        if filename.endswith(".json"):
            snapshot_date = filename.split("_")[-1].replace(".json", "")
            try:
                if not is_snapshot_relevant(snapshot_date, start_dates):
                    file_path = os.path.join(snapshot_dir, filename)
                    os.remove(file_path)
                    print(f"Deleted irrelevant snapshot: {file_path}")
                else:
                    print(f"Snapshot is relevant: {filename}")
            except Exception as e:
                print(f"Error processing file '{filename}': {e}")

if __name__ == "__main__":
    import sys

    # allow optional directory argument
    snapshot_dir = sys.argv[1] if len(sys.argv) > 1 else "daily_snapshots"

    # Load epoch start dates
    start_dates = load_epoch_schedule()

    # Clean snapshots
    clean_snapshots(start_dates, snapshot_dir=snapshot_dir)
