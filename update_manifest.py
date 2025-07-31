import os
import json

# Change to the current_vote_power directory
docs_dir = r"c:\Users\tripk\Dropbox\Documents\github\flare-ftso-snapshot\docs\current_vote_power"
os.chdir(docs_dir)

# Get all files and sort them
flare_files = sorted([f for f in os.listdir('.') if f.startswith('flare_vp_') and f.endswith('.json')])
songbird_files = sorted([f for f in os.listdir('.') if f.startswith('songbird_vp_') and f.endswith('.json')])

# Create manifest
manifest = {
    "flare": flare_files,
    "songbird": songbird_files
}

# Write manifest
with open('manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"Updated manifest.json with {len(flare_files)} flare files and {len(songbird_files)} songbird files")
