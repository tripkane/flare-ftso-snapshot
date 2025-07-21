import requests
import json
from typing import Dict, List, Any

# Your Ankr RPC endpoint
ANKR_API_KEY = "0eb7f4b8bae149b70576678cbe1b2d892a1edb981112e5005c054391f384ed9a"
FLARE_RPC_URL = f"https://rpc.ankr.com/flare/{ANKR_API_KEY}"

# Known Flare system contract addresses (need to verify these)
FLARE_CONTRACTS = {
    # These are commonly known Flare contract addresses - may need updating
    "VoterRegistry": "0x0000000000000000000000000000000000000007",  # FSP contract
    "FlareSystemsManager": "0x0000000000000000000000000000000000000008",  # FSP contract
    "VoterWhitelister": "0x0000000000000000000000000000000000000009",  # FSP contract
    
    # Legacy FTSO contracts (if still relevant)
    "FtsoManager": "0x0000000000000000000000000000000000000003",  # Legacy FTSO
    "VoterWhitelistManager": "0x0000000000000000000000000000000000000004",  # Legacy FTSO
}

def make_rpc_call(method: str, params: List[Any] = None) -> Dict[Any, Any]:
    """Make a JSON-RPC call to the Flare network via Ankr"""
    if params is None:
        params = []
    
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    response = requests.post(FLARE_RPC_URL, json=payload)
    response.raise_for_status()
    return response.json()

def check_contract_exists(address: str) -> bool:
    """Check if a contract exists at the given address"""
    try:
        result = make_rpc_call("eth_getCode", [address, "latest"])
        code = result["result"]
        return code != "0x" and len(code) > 2
    except:
        return False

def find_active_contracts():
    """Find which of our known contracts actually exist"""
    print("=== Checking Contract Addresses ===")
    active_contracts = {}
    
    for name, address in FLARE_CONTRACTS.items():
        exists = check_contract_exists(address)
        status = "✓ Active" if exists else "✗ Not found"
        print(f"{name}: {address} - {status}")
        if exists:
            active_contracts[name] = address
    
    return active_contracts

def search_for_ftso_events():
    """Search for FTSO-related events in recent blocks"""
    print("\n=== Searching for FTSO/FSP Events ===")
    
    # Common event signatures for vote power and delegation
    event_signatures = {
        "DelegateVotes": "0x...",  # Placeholder - need actual signature
        "VotePowerChanged": "0x...",  # Placeholder - need actual signature
        "ProviderRegistered": "0x...",  # Placeholder - need actual signature
    }
    
    try:
        # Search recent blocks for any FTSO-related activity
        result = make_rpc_call("eth_getLogs", [{
            "fromBlock": hex(44880900),  # Recent blocks
            "toBlock": "latest",
            # We'll search all logs for now to find patterns
        }])
        
        logs = result["result"]
        print(f"Found {len(logs)} total logs in recent blocks")
        
        # Group logs by contract address
        contract_activity = {}
        for log in logs:
            addr = log["address"]
            contract_activity[addr] = contract_activity.get(addr, 0) + 1
        
        # Show most active contracts
        print("\nMost active contracts:")
        for addr, count in sorted(contract_activity.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {addr}: {count} events")
        
        return logs
    except Exception as e:
        print(f"Failed to search events: {e}")
        return []

def analyze_sample_data():
    """Look at your existing scraped data to understand the target format"""
    print("\n=== Target Data Format Analysis ===")
    
    # This would be the structure we need to replicate from blockchain data
    target_format = {
        "timestamp": "2025-07-21T14-30-00Z",
        "network": "flare",
        "providers": [
            {
                "name": "Provider Name",
                "vote_power": 15.5  # Percentage
            }
        ]
    }
    
    print("Target format we need to replicate:")
    print(json.dumps(target_format, indent=2))
    
    print("\nQuestions to resolve:")
    print("1. How to get provider names from addresses?")
    print("2. How to calculate vote power percentages?")
    print("3. Which epoch/block should we query for current data?")

def main():
    """Main exploration function"""
    print("Exploring Flare Network for Vote Power Data")
    print("=" * 50)
    
    # Check known contract addresses
    active_contracts = find_active_contracts()
    
    # Search for relevant events
    search_for_ftso_events()
    
    # Show target data format
    analyze_sample_data()
    
    print("\n" + "=" * 50)
    print("Recommended Next Steps:")
    print("1. Find the correct FSP contract addresses from Flare documentation")
    print("2. Identify the exact method calls needed for vote power data")
    print("3. Create a mapping from provider addresses to human-readable names")
    print("4. Implement historical data collection for all epochs")

if __name__ == "__main__":
    main()
