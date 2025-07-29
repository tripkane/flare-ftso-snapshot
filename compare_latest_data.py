#!/usr/bin/env python3
"""
Compare the latest RPC and scraped data to verify accuracy.
"""

import json
import glob
from datetime import datetime
from provider_names import get_provider_name


def find_latest_files():
    """Find the latest RPC and scraped files."""
    current_files = glob.glob('current_vote_power/*.json')
    
    rpc_files = []
    scraped_files = []
    
    print("Analyzing files...")
    
    for file in current_files:
        try:
            with open(file, 'r') as f:
                content = f.read(100)  # Just read first 100 chars to check
                if 'NORTSO' in content or 'Flare Oracle' in content:
                    rpc_files.append(file)
                elif content.strip() and not content.startswith('Provider_0x'):
                    scraped_files.append(file)
        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue
    
    # Get latest files
    latest_rpc = sorted(rpc_files)[-1] if rpc_files else None
    latest_scraped = sorted(scraped_files)[-1] if scraped_files else None
    
    return latest_rpc, latest_scraped


def load_data(filepath):
    """Load and validate JSON data."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        print(f"JSON decode error in {filepath}: {e}")
        return None
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def compare_vote_power_data(rpc_file, scraped_file):
    """Compare vote power data between RPC and scraped sources."""
    
    print(f"\n=== Comparing Data Files ===")
    print(f"RPC File:     {rpc_file}")
    print(f"Scraped File: {scraped_file}")
    
    # Load data
    rpc_data = load_data(rpc_file)
    scraped_data = load_data(scraped_file)
    
    if not rpc_data:
        print("❌ Failed to load RPC data")
        return
        
    if not scraped_data:
        print("❌ Failed to load scraped data")
        return
    
    print("✅ Both files loaded successfully")
    
    # Extract provider data
    rpc_providers = rpc_data.get('providers', [])
    scraped_providers = scraped_data.get('providers', [])
    
    print(f"\nRPC Providers: {len(rpc_providers)}")
    print(f"Scraped Providers: {len(scraped_providers)}")
    
    # Show top providers from each
    print(f"\n=== Top 5 RPC Providers ===")
    for i, provider in enumerate(rpc_providers[:5]):
        name = provider.get('name', 'Unknown')
        vote_power = provider.get('vote_power', 0)
        percentage = provider.get('vote_power_percentage', 0)
        print(f"{i+1}. {name}: {vote_power:,} ({percentage:.2f}%)")
    
    print(f"\n=== Top 5 Scraped Providers ===")
    for i, provider in enumerate(scraped_providers[:5]):
        name = provider.get('name', provider.get('provider_name', 'Unknown'))
        vote_power = provider.get('vote_power', 0) or 0
        percentage = provider.get('vote_power_percentage', 0) or 0
        print(f"{i+1}. {name}: {vote_power:,} ({percentage:.2f}%)")
    
    # Compare specific providers by trying to match addresses or names
    print(f"\n=== Provider Comparison ===")
    
    # Build lookup for scraped data
    scraped_lookup = {}
    for provider in scraped_providers:
        address = provider.get('provider_address', '').lower()
        name = provider.get('name', provider.get('provider_name', 'Unknown'))
        if address:
            scraped_lookup[address] = provider
    
    matches = 0
    differences = []
    
    for rpc_provider in rpc_providers[:10]:  # Check top 10
        rpc_name = rpc_provider.get('name', 'Unknown')
        rpc_address = rpc_provider.get('provider_address', '').lower()
        rpc_percentage = rpc_provider.get('vote_power_percentage', 0)
        
        if rpc_address in scraped_lookup:
            scraped_provider = scraped_lookup[rpc_address]
            scraped_percentage = scraped_provider.get('vote_power_percentage', 0)
            
            diff = abs(rpc_percentage - scraped_percentage)
            differences.append(diff)
            matches += 1
            
            status = "✅" if diff < 0.1 else "⚠️" if diff < 1.0 else "❌"
            print(f"{status} {rpc_name}")
            print(f"   RPC: {rpc_percentage:.2f}%  |  Scraped: {scraped_percentage:.2f}%  |  Diff: {diff:.3f}%")
    
    print(f"\n=== Summary ===")
    print(f"Matched providers: {matches}")
    if differences:
        avg_diff = sum(differences) / len(differences)
        max_diff = max(differences)
        print(f"Average difference: {avg_diff:.3f}%")
        print(f"Maximum difference: {max_diff:.3f}%")
        
        if avg_diff < 0.1:
            print("🎉 EXCELLENT: Data matches very closely!")
        elif avg_diff < 1.0:
            print("✅ GOOD: Data matches reasonably well")
        else:
            print("⚠️ WARNING: Significant differences detected")
    
    # Check total vote power
    rpc_total = rpc_data.get('total_vote_power', 0)
    scraped_total = scraped_data.get('total_vote_power', 0)
    
    if rpc_total and scraped_total:
        total_diff = abs(rpc_total - scraped_total) / max(rpc_total, scraped_total) * 100
        print(f"\nTotal Vote Power:")
        print(f"RPC: {rpc_total:,}")
        print(f"Scraped: {scraped_total:,}")
        print(f"Difference: {total_diff:.3f}%")


def main():
    print("Finding latest data files...")
    
    latest_rpc, latest_scraped = find_latest_files()
    
    if not latest_rpc:
        print("❌ No RPC files found")
        return
        
    if not latest_scraped:
        print("❌ No scraped files found")
        return
    
    compare_vote_power_data(latest_rpc, latest_scraped)
    
    # Also show a sample RPC file content to verify it has real names
    print(f"\n=== Sample RPC Data ===")
    rpc_data = load_data(latest_rpc)
    if rpc_data and 'providers' in rpc_data:
        print("Top 3 providers with human-readable names:")
        for i, provider in enumerate(rpc_data['providers'][:3]):
            print(f"{i+1}. {provider.get('name', 'Unknown')}: {provider.get('vote_power_percentage', 0):.2f}%")


if __name__ == "__main__":
    main()
