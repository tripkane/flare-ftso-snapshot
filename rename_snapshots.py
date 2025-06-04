import os

folder = "daily_snapshots"
for filename in os.listdir(folder):
    if filename.startswith("ftso_snapshot_") and filename.endswith(".json"):
        new_name = "flare_" + filename
        os.rename(os.path.join(folder, filename), os.path.join(folder, new_name))
        print(f"Renamed {filename} -> {new_name}")
