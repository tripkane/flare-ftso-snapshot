import json
import glob

print('=== DETAILED DATA VALIDATION: RPC vs SCRAPED ===')

# Get the most recent RPC data (files with real provider names)
rpc_files = [f for f in glob.glob('current_vote_power/*.json') if 'NORTSO' in open(f).read() or 'Flare Oracle' in open(f).read()]
if rpc_files:
    rpc_files.sort()
    with open(rpc_files[-1], 'r') as f:
        rpc_data = json.load(f)
    print('RPC Data from:', rpc_files[-1])
else:
    print('No RPC data found')
    exit()

# Get the most recent scraped data (non-RPC files)
scraped_files = [f for f in glob.glob('current_vote_power/*.json') if 'Provider_0x' not in open(f).read() and 'NORTSO' not in open(f).read()]
if scraped_files:
    scraped_files.sort()
    with open(scraped_files[-1], 'r') as f:
        scraped_data = json.load(f)
    print('Scraped Data from:', scraped_files[-1])
else:
    print('No scraped data found')
    exit()

print()
print('=== PROVIDER COMPARISON ===')
print('Provider Name          | RPC Vote Power | Scraped Vote Power | Difference')
print('-' * 75)

# Create lookup for scraped data by name
scraped_lookup = {p['name']: p for p in scraped_data['providers']}

for rpc_provider in rpc_data['providers']:
    name = rpc_provider['name']
    rpc_vote_power = rpc_provider.get('vote_power', 0)
    
    # Find matching scraped provider
    scraped_provider = scraped_lookup.get(name)
    if scraped_provider:
        scraped_vote_power = scraped_provider.get('vote_power', 0)
        
        # Calculate difference
        if scraped_vote_power > 0:
            vote_power_diff = abs(rpc_vote_power - scraped_vote_power)
            diff_str = f'{vote_power_diff:.1f}%'
        else:
            diff_str = 'N/A'
        
        print(f'{name:20} | {rpc_vote_power:12.1f}% | {scraped_vote_power:16.1f}% | {diff_str}')
    else:
        print(f'{name:20} | {rpc_vote_power:12.1f}% | NOT FOUND          | N/A')

print()
print('=== SUMMARY ===')
print('RPC Providers:', len(rpc_data['providers']))
print('Scraped Providers:', len(scraped_data['providers']))
print('RPC Timestamp:', rpc_data.get('timestamp', 'Unknown'))
print('Scraped Timestamp:', scraped_data.get('timestamp', 'Unknown'))

# Check reward rates if available
print()
print('=== REWARD RATE COMPARISON ===')
for rpc_provider in rpc_data['providers']:
    name = rpc_provider['name']
    rpc_reward = rpc_provider.get('reward_rate', 'N/A')
    
    scraped_provider = scraped_lookup.get(name)
    if scraped_provider:
        scraped_reward = scraped_provider.get('reward_rate', 'N/A')
        print(f'{name:20} | RPC: {str(rpc_reward):10} | Scraped: {str(scraped_reward):10}')

# Show top scraped providers for comparison
print()
print('=== TOP SCRAPED PROVIDERS FOR REFERENCE ===')
top_scraped = sorted(scraped_data['providers'], key=lambda x: x.get('vote_power', 0), reverse=True)[:10]
for i, provider in enumerate(top_scraped):
    vote_power = provider.get('vote_power', 0)
    name = provider.get('name', 'Unknown')
    print(f'{i+1:2d}. {name:20} | {vote_power:6.1f}%')
