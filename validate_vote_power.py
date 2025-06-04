import os
import json

def validate_vote_power(directory="daily_snapshots"):
    """Check if every vote_power entry has an even number of digits."""
    all_valid = True  # Flag to track if all entries are valid
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            print(f"Checking file: {filename}")
            for provider in data.get("providers", []):
                vote_power = str(provider.get("vote_power", ""))
                if len(vote_power) % 2 != 0:
                    print(f"Odd-length vote_power found in {filename}: {vote_power} (Provider: {provider.get('name', 'Unknown')})")
                    all_valid = False  # Mark as invalid if an odd-length entry is found

    if all_valid:
        print("All vote_power entries have an even number of characters.")

if __name__ == "__main__":
    validate_vote_power()
