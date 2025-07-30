import json

try:
    with open('docs/current_vote_power/manifest.json', 'r') as f:
        manifest = json.load(f)
    print('Manifest loaded successfully')
    print(f'Keys: {list(manifest.keys())}')
    print(f'Flare entries: {len(manifest.get("flare", []))}')
except Exception as e:
    print(f'Error loading manifest: {e}')
    # Try to find the problematic part
    with open('docs/current_vote_power/manifest.json', 'r') as f:
        content = f.read()
    
    # Check for merge conflict markers
    if '<<<<<<< ' in content:
        print('Found merge conflict markers!')
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '<<<<<<< ' in line or '>>>>>>> ' in line or '=======' in line:
                print(f'Line {i+1}: {line}')
