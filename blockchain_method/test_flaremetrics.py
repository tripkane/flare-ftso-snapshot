import requests
import json
from typing import Dict

def scrape_flaremetrics_simple():
    """Simple test to see FlareMetrics page structure"""
    try:
        response = requests.get("https://flaremetrics.io/", timeout=30)
        
        if response.status_code == 200:
            content = response.text
            
            # Look for specific provider names we know exist
            test_providers = ["Bifrost Wallet", "Flare.Space", "AlphaOracle", "Atlas TSO"]
            
            found_providers = []
            for provider in test_providers:
                if provider in content:
                    found_providers.append(provider)
                    print(f"✓ Found: {provider}")
                else:
                    print(f"✗ Not found: {provider}")
            
            print(f"\nFound {len(found_providers)} of {len(test_providers)} test providers")
            
            # Save a sample of the content to see structure
            with open('flaremetrics_sample.html', 'w', encoding='utf-8') as f:
                f.write(content[:10000])  # First 10k chars
            
            print("Saved sample HTML to flaremetrics_sample.html")
            
        else:
            print(f"HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_flaremetrics_simple()
