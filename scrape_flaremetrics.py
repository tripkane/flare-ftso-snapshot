import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict

def scrape_flaremetrics_providers() -> Dict[str, str]:
    """
    Scrape FTSO provider names from FlareMetrics.io using BeautifulSoup
    """
    provider_names = {}
    
    try:
        print("Fetching FlareMetrics.io page...")
        response = requests.get("https://flaremetrics.io/", timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for table elements
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables")
            
            for i, table in enumerate(tables):
                print(f"\nAnalyzing table {i+1}...")
                
                # Get all rows
                rows = table.find_all('tr')
                print(f"  Found {len(rows)} rows")
                
                for j, row in enumerate(rows[:5]):  # Check first 5 rows
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        cell_texts = [cell.get_text(strip=True) for cell in cells]
                        print(f"    Row {j}: {cell_texts[:3]}")  # Show first 3 cells
                        
                        # Look for patterns: provider name + address
                        for k, cell_text in enumerate(cell_texts):
                            if cell_text.startswith('0x') and len(cell_text) == 42:
                                # This looks like an address
                                address = cell_text.lower()
                                
                                # Try to find provider name in nearby cells
                                if k > 0:  # Name might be in previous cell
                                    name = cell_texts[k-1]
                                    if name and not name.isdigit() and len(name) > 2:
                                        provider_names[address] = name
                                        print(f"      ✓ Found: {address} -> {name}")
                                
                                if k < len(cell_texts) - 1:  # Name might be in next cell
                                    name = cell_texts[k+1]
                                    if name and not name.isdigit() and len(name) > 2:
                                        if address not in provider_names:  # Don't overwrite
                                            provider_names[address] = name
                                            print(f"      ✓ Found: {address} -> {name}")
            
            print(f"\nTotal providers found: {len(provider_names)}")
            
            # If no table data found, look for JSON data in script tags
            if not provider_names:
                print("\nLooking for JSON data in script tags...")
                scripts = soup.find_all('script')
                
                for script in scripts:
                    if script.string:
                        # Look for provider data patterns
                        if 'provider' in script.string.lower() or '0x' in script.string:
                            # Try to extract JSON
                            json_matches = re.findall(r'\{[^{}]*"(?:address|provider)"[^{}]*\}', script.string)
                            for match in json_matches[:3]:  # Show first 3 matches
                                print(f"    JSON candidate: {match[:100]}...")
            
        else:
            print(f"HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    return provider_names

def test_known_providers():
    """Test extraction with known provider names"""
    providers = scrape_flaremetrics_providers()
    
    # Check if we found any known providers
    known_names = ["Bifrost Wallet", "Flare.Space", "AlphaOracle", "Atlas TSO"]
    found_known = []
    
    for address, name in providers.items():
        if name in known_names:
            found_known.append(name)
            print(f"✓ Successfully found known provider: {name} -> {address}")
    
    print(f"\nFound {len(found_known)} of {len(known_names)} known providers")
    
    # Save results
    if providers:
        with open('scraped_providers.json', 'w') as f:
            json.dump(providers, f, indent=2)
        print(f"Saved {len(providers)} providers to scraped_providers.json")
    
    return providers

if __name__ == "__main__":
    test_known_providers()
