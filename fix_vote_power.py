import os
import json


def maybe_split(vp_raw: str):
    """Return tuple of (vote_power, vote_power_locked) if vp_raw appears doubled."""
    digits = vp_raw.replace(",", "")
    if digits.isdigit() and len(digits) % 2 == 0:
        half = len(digits) // 2
        first, second = digits[:half], digits[half:]
        if first == second:
            return int(first), int(second)
    return None


def fix_vote_power(directory="daily_snapshots"):
    for root, _, files in os.walk(directory):
        for filename in sorted(files):
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)
            with open(file_path, "r") as f:
                data = json.load(f)

            changed = False
            for provider in data.get("providers", []):
                vp_raw = str(provider.get("vote_power", ""))
                locked_raw = str(provider.get("vote_power_locked", ""))

                # Detect doubled numbers (vote_power == vote_power_locked and digits repeated)
                if vp_raw == locked_raw:
                    result = maybe_split(vp_raw)
                    if result:
                        provider["vote_power"], provider["vote_power_locked"] = result
                        changed = True

            if changed:
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"Fixed: {file_path}")


if __name__ == "__main__":
    for d in ["daily_snapshots", os.path.join("docs", "daily_snapshots")]:
        if os.path.isdir(d):
            fix_vote_power(d)
