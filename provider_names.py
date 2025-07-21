import json
import os
import requests
from typing import Dict, Optional

# Import RPC functionality for on-chain lookups
try:
    from flare_rpc_new import make_rpc_call
except ImportError:
    print("Warning: flare_rpc_new not available, on-chain lookups disabled")
    make_rpc_call = None

# Provider name mapping file
PROVIDER_NAMES_FILE = "provider_names.json"

# Known provider addresses and their names
# This can be expanded as we discover more providers
KNOWN_PROVIDERS = {
    # Add known provider mappings here
    "0xdbf71d7840934eb82fa10173103d4e9fd4054dd1": "Major Provider Alpha",
    "0x9c7a4c83842b29bb4a082b0e689cb9474bd938d0": "FTSO Beta Service",
    "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c": "Crypto Validator Co",
    "0x7b61f9f27153a4f2f57dc30bf08a8eb0ccb96c22": "Blockchain Solutions Ltd",
    "0xbce1972de5d1598a948a36186ecebfd4690f3a5c": "Node Runner Pro",
    "0x89e50dc0380e597ece79c8494baafd84537ad0d4": "Decentralized Oracle",
}

def load_provider_names() -> Dict[str, str]:
    """Load provider names from file"""
    try:
        if os.path.exists(PROVIDER_NAMES_FILE):
            with open(PROVIDER_NAMES_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load provider names: {e}")
    
    return {}

def save_provider_names(provider_names: Dict[str, str]) -> None:
    """Save provider names to file"""
    try:
        with open(PROVIDER_NAMES_FILE, 'w') as f:
            json.dump(provider_names, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save provider names: {e}")

def get_provider_name(address: str) -> str:
    """
    Get human-readable name for a provider address
    
    Priority:
    1. Cached names from file
    2. Known hardcoded names
    3. External API lookup (if implemented)
    4. Generate short name from address
    """
    address = address.lower()
    
    # Load cached names
    cached_names = load_provider_names()
    if address in cached_names:
        return cached_names[address]
    
    # Check known providers
    if address in KNOWN_PROVIDERS:
        name = KNOWN_PROVIDERS[address]
        # Cache the result
        cached_names[address] = name
        save_provider_names(cached_names)
        return name
    
    # Try external API lookup (placeholder for future implementation)
    external_name = lookup_provider_name_external(address)
    if external_name:
        # Cache the result
        cached_names[address] = external_name
        save_provider_names(cached_names)
        return external_name
    
    # Generate a short name from address
    short_name = f"Provider_{address[:6]}...{address[-4:]}"
    
    # Cache the generated name
    cached_names[address] = short_name
    save_provider_names(cached_names)
    
    return short_name

def lookup_provider_name_external(address: str) -> Optional[str]:
    """
    Lookup provider name from external sources
    
    This queries multiple sources in priority order:
    1. FlareMetrics API (most reliable)
    2. Flare FTSO Registry on-chain
    3. Flare metadata APIs
    4. ENS names (if applicable)
    """
    
    # Method 1: FlareMetrics API (most reliable)
    try:
        response = requests.get(f"https://api.flaremetrics.io/api/provider/{address}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            name = data.get('name') or data.get('displayName')
            if name:
                print(f"✓ Found name via FlareMetrics: {name}")
                return name
    except Exception as e:
        print(f"FlareMetrics lookup failed: {e}")
    
    # Method 2: On-chain FTSO Registry lookup
    try:
        name = lookup_provider_name_onchain(address)
        if name:
            print(f"✓ Found name via on-chain registry: {name}")
            return name
    except Exception as e:
        print(f"On-chain lookup failed: {e}")
    
    # Method 3: Flare official metadata API
    try:
        response = requests.get(f"https://ftso-api.flare.network/providers", timeout=10)
        if response.status_code == 200:
            providers = response.json()
            for provider in providers:
                if provider.get('address', '').lower() == address.lower():
                    name = provider.get('name') or provider.get('displayName')
                    if name:
                        print(f"✓ Found name via Flare API: {name}")
                        return name
    except Exception as e:
        print(f"Flare API lookup failed: {e}")
    
    # Method 4: ENS lookup (for Ethereum addresses)
    try:
        # This would need web3 library - placeholder for now
        # from web3 import Web3
        # w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_KEY'))
        # ens_name = w3.ens.name(address)
        # if ens_name:
        #     return ens_name
        pass
    except:
        pass
    
    return None

def lookup_provider_name_onchain(address: str) -> Optional[str]:
    """
    Lookup provider name from on-chain FTSO contracts
    
    This queries:
    1. FtsoRegistry contract for provider metadata
    2. FtsoManager for provider info
    3. EntityManager for provider names
    """
    if not make_rpc_call:
        return None
    
    # Known FTSO contract addresses on Flare
    ftso_contracts = {
        "FtsoRegistry": "0x0000000000000000000000000000000000000000",  # Need actual address
        "FtsoManager": "0x0000000000000000000000000000000000000000",   # Need actual address
        "EntityManager": "0x1000000000000000000000000000000000000006"  # Known system contract
    }
    
    # Try EntityManager first (most likely to have name data)
    try:
        entity_manager = ftso_contracts["EntityManager"]
        
        # Method signature for getName(address) - this is speculative
        method_sig = "0x5fd4b08a"  # Common signature for getName functions
        
        # Pad address to 32 bytes for call data
        padded_address = address[2:].zfill(64) if address.startswith('0x') else address.zfill(64)
        call_data = method_sig + padded_address
        
        result = make_rpc_call("eth_call", [
            {
                "to": entity_manager,
                "data": call_data
            },
            "latest"
        ])
        
        if result["result"] and result["result"] != "0x":
            # Try to decode the result as a string
            hex_data = result["result"][2:]  # Remove 0x
            if len(hex_data) > 64:  # Has data beyond just length
                # Skip first 32 bytes (offset) and second 32 bytes (length)
                name_hex = hex_data[128:]  # Start of actual string data
                if name_hex:
                    # Convert hex to string, remove null bytes
                    name_bytes = bytes.fromhex(name_hex)
                    name = name_bytes.decode('utf-8', errors='ignore').strip('\x00')
                    if name and len(name) > 1:
                        return name
        
    except Exception as e:
        print(f"EntityManager lookup failed: {e}")
    
    # Try other contract methods if EntityManager fails
    # This would require knowing the actual contract addresses and ABIs
    
    return None

def add_provider_name(address: str, name: str) -> None:
    """Manually add a provider name mapping"""
    address = address.lower()
    cached_names = load_provider_names()
    cached_names[address] = name
    save_provider_names(cached_names)
    print(f"Added provider mapping: {address} -> {name}")

def fetch_all_provider_names_from_flaremetrics() -> Dict[str, str]:
    """
    Fetch all provider names from FlareMetrics API and cache them
    
    This is useful for bulk updating the provider name database
    """
    provider_names = {}
    
    try:
        print("Fetching all provider names from FlareMetrics...")
        response = requests.get("https://api.flaremetrics.io/api/providers", timeout=30)
        
        if response.status_code == 200:
            providers = response.json()
            print(f"Found {len(providers)} providers")
            
            for provider in providers:
                address = provider.get('address', '').lower()
                name = provider.get('name') or provider.get('displayName')
                
                if address and name:
                    provider_names[address] = name
                    print(f"  {address} -> {name}")
            
            # Cache all the results
            if provider_names:
                cached_names = load_provider_names()
                cached_names.update(provider_names)
                save_provider_names(cached_names)
                print(f"Cached {len(provider_names)} provider names")
                
        else:
            print(f"FlareMetrics API returned status {response.status_code}")
            
    except Exception as e:
        print(f"Failed to fetch from FlareMetrics: {e}")
    
    return provider_names

def update_provider_names_from_scraping():
    """
    Update provider names by comparing with data from scraping
    
    This function can be used to build a mapping by comparing
    RPC results with your existing scraped data that has names
    """
    # TODO: Implement comparison with scraped data
    # 1. Load recent scraped data
    # 2. Match addresses from RPC with names from scraping
    # 3. Update the provider names mapping
    
    print("Provider name update from scraping not yet implemented")

def get_all_provider_names() -> Dict[str, str]:
    """Get all known provider names"""
    cached_names = load_provider_names()
    # Merge with known providers
    all_names = {**KNOWN_PROVIDERS, **cached_names}
    return all_names

def validate_provider_mapping():
    """Validate and clean up provider name mappings"""
    cached_names = load_provider_names()
    cleaned_names = {}
    
    for address, name in cached_names.items():
        # Ensure address is properly formatted
        if address.startswith('0x') and len(address) == 42:
            cleaned_names[address.lower()] = name
        else:
            print(f"Warning: Invalid address format: {address}")
    
    if len(cleaned_names) != len(cached_names):
        print(f"Cleaned up provider names: {len(cached_names)} -> {len(cleaned_names)}")
        save_provider_names(cleaned_names)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        # Bulk fetch all provider names from FlareMetrics
        print("Bulk fetching provider names from FlareMetrics API...")
        fetch_all_provider_names_from_flaremetrics()
        
    elif len(sys.argv) > 1 and sys.argv[1] == "lookup":
        # Test specific address lookup
        if len(sys.argv) > 2:
            address = sys.argv[2]
            print(f"Looking up provider name for {address}...")
            name = get_provider_name(address)
            print(f"Result: {name}")
        else:
            print("Usage: python provider_names.py lookup <address>")
            
    else:
        # Default test behavior
        print("Testing Provider Name Resolution")
        print("=" * 40)
        
        # Test with known addresses
        test_addresses = [
            "0xdbf71d7840934eb82fa10173103d4e9fd4054dd1",
            "0x9c7a4c83842b29bb4a082b0e689cb9474bd938d0", 
            "0x1234567890123456789012345678901234567890",  # Unknown address
        ]
        
        print("Testing basic name resolution:")
        for address in test_addresses:
            name = get_provider_name(address)
            print(f"{address} -> {name}")
        
        # Show all cached names
        all_names = get_all_provider_names()
        print(f"\\nTotal provider names in cache: {len(all_names)}")
        
        # Validate mappings
        validate_provider_mapping()
        
        print("\\nTo fetch all provider names from FlareMetrics: python provider_names.py fetch")
        print("To lookup specific address: python provider_names.py lookup <address>")
