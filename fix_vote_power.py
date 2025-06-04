import os
import json

def fix_vote_power(directory="daily_snapshots"):
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as f:
                data = json.load(f)
            changed = False
            for provider in data.get("providers", []):
                vp = str(provider.get("vote_power", ""))
                if vp and len(vp) % 2 == 0:
                    mid = len(vp) // 2
                    vp1 = vp[:mid].replace(",", "")
                    vp2 = vp[mid:].replace(",", "")
                    # Only update if not already numeric
                    if not (provider.get("vote_power_locked") and isinstance(provider["vote_power"], int)):
                        provider["vote_power"] = int(vp1) if vp1.isdigit() else 0
                        provider["vote_power_locked"] = int(vp2) if vp2.isdigit() else 0
                        changed = True
            if changed:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Fixed: {filename}")

if __name__ == "__main__":
    fix_vote_power()
