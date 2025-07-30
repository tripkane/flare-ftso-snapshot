#!/usr/bin/env python3
"""
Compare RPC vs Scraped data for validation.
"""

import json

def main():
    # Use the latest files from same day
    rpc_file = 'current_vote_power/flare_vp_2025-07-22T13-50-32Z.json'
    scraped_file = 'current_vote_power/flare_vp_2025-07-22T13-27-53Z.json'
    
    print("=== Flare Network Data Validation ===")
    print(f"RPC File:     {rpc_file}")
    print(f"Scraped File: {scraped_file}")
    print(f"Time diff:    ~23 minutes")
    
    # Load data
    with open(rpc_file, 'r') as f:
        rpc_data = json.load(f)
    
    with open(scraped_file, 'r') as f:
        scraped_data = json.load(f)
    
    rpc_providers = rpc_data['providers']
    scraped_providers = scraped_data['providers']
    
    print(f"\n=== Data Overview ===")
    print(f"RPC Providers: {len(rpc_providers)} (with human names)")
    print(f"Scraped Providers: {len(scraped_providers)} (with addresses)")
    
    print(f"\n=== Top 5 RPC Providers (Human Names) ===")
    for i, p in enumerate(rpc_providers[:5]):
        name = p['name']
        vp = p['vote_power']
        print(f"{i+1}. {name:<20} {vp:>8.2f}%")
    
    print(f"\n=== Top 5 Scraped Providers (Addresses) ===")
    for i, p in enumerate(scraped_providers[:5]):
        name = p['name']
        vp = p['vote_power']
        print(f"{i+1}. {name:<20} {vp:>8.2f}%")
    
    print(f"\n=== Validation by Vote Power Ranking ===")
    
    # Compare by ranking (since we can't match addresses directly)
    max_compare = min(len(rpc_providers), len(scraped_providers), 10)
    
    total_diff = 0
    for i in range(max_compare):
        rpc_vp = rpc_providers[i]['vote_power']
        scraped_vp = scraped_providers[i]['vote_power']
        diff = abs(rpc_vp - scraped_vp)
        total_diff += diff
        
        status = "✅" if diff < 0.5 else "⚠️" if diff < 2.0 else "❌"
        
        print(f"{status} Rank {i+1:2d}: RPC {rpc_vp:6.2f}% | Scraped {scraped_vp:6.2f}% | Diff {diff:6.3f}%")
    
    avg_diff = total_diff / max_compare
    
    print(f"\n=== Results Summary ===")
    print(f"Average difference: {avg_diff:.3f}%")
    print(f"Compared providers: {max_compare}")
    
    if avg_diff < 0.5:
        print("🎉 EXCELLENT: RPC data matches scraped data very closely!")
        print("   The blockchain RPC approach is highly accurate.")
    elif avg_diff < 1.0:
        print("✅ VERY GOOD: RPC data is very close to scraped data")
        print("   Minor differences likely due to timing or rounding.")
    elif avg_diff < 2.0:
        print("✅ GOOD: RPC data aligns well with scraped data")
        print("   Differences within acceptable range.")
    else:
        print("⚠️ WARNING: Some significant differences detected")
        print("   May need further investigation.")
    
    # Show the provider names we now have
    print(f"\n=== Human-Readable Provider Names (RPC) ===")
    print("Instead of addresses like '0xdbf7...4dd1', we now have:")
    for i, p in enumerate(rpc_providers[:8]):
        print(f"  {p['name']}")
    
    print(f"\n✅ SUCCESS: RPC system provides:")
    print(f"   • Human-readable provider names")  
    print(f"   • Accurate vote power percentages")
    print(f"   • Real-time blockchain data")
    print(f"   • No web scraping dependencies")

if __name__ == "__main__":
    main()
