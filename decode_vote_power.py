import requests
import json
from typing import Dict, List, Any

# Your Ankr RPC endpoint  
ANKR_API_KEY = "0eb7f4b8bae149b70576678cbe1b2d892a1edb981112e5005c054391f384ed9a"
FLARE_RPC_URL = f"https://rpc.ankr.com/flare/{ANKR_API_KEY}"

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

def decode_vote_power_events():
    """Decode the vote power-related events we found"""
    print("=== Decoding Vote Power Events ===")
    
    # Contract that seems to have vote power data
    vote_power_contract = "0x1000000000000000000000000000000000000002"
    event_signature = "0xe7aa66356adbd5e839ef210626f6d8f6f72109c17fadf4c4f9ca82b315ae79b4"
    
    try:
        result = make_rpc_call("eth_getLogs", [{
            "address": vote_power_contract,
            "topics": [event_signature],
            "fromBlock": hex(44880900),
            "toBlock": "latest"
        }])
        
        logs = result["result"]
        print(f"Found {len(logs)} vote power events")
        
        # Decode the vote power data
        providers_data = []
        total_vote_power = 0
        
        for log in logs[:20]:  # Process first 20 for analysis
            data = log["data"]
            if len(data) == 130:  # 0x + 128 hex chars = 2 * 32-byte values
                # Extract address (first 32 bytes, but address is in last 20 bytes)
                address_hex = data[26:66]  # Skip 0x and padding, get 40 chars
                address = "0x" + address_hex
                
                # Extract vote power (second 32 bytes)
                vote_power_hex = data[66:130]
                vote_power = int(vote_power_hex, 16)
                
                providers_data.append({
                    "address": address,
                    "vote_power": vote_power,
                    "block": int(log["blockNumber"], 16),
                    "tx": log["transactionHash"]
                })
                
                total_vote_power += vote_power
                
                print(f"Provider: {address}, Vote Power: {vote_power:,}")
        
        # Calculate percentages
        print(f"\nTotal Vote Power: {total_vote_power:,}")
        print(f"\nTop 10 by percentage:")
        
        for provider in sorted(providers_data, key=lambda x: x["vote_power"], reverse=True)[:10]:
            percentage = (provider["vote_power"] / total_vote_power) * 100 if total_vote_power > 0 else 0
            print(f"  {provider['address']}: {percentage:.2f}%")
        
        return providers_data
        
    except Exception as e:
        print(f"Failed to decode vote power events: {e}")
        return []

def decode_epoch_events():
    """Decode epoch-related events"""
    print(f"\n=== Decoding Epoch Events ===")
    
    epoch_contract = "0xdbf71d7840934eb82fa10173103d4e9fd4054dd1"
    event_signature = "0x63db91b14b3d088c677f046180aefcea7a236649704d90ce810cde455d38d936"
    
    try:
        result = make_rpc_call("eth_getLogs", [{
            "address": epoch_contract,
            "topics": [event_signature],
            "fromBlock": hex(44880900),
            "toBlock": "latest"
        }])
        
        logs = result["result"]
        print(f"Found {len(logs)} epoch-related events")
        
        epoch_data = []
        for log in logs[:10]:
            if len(log["topics"]) >= 3:
                # Topic 1 appears to be epoch number
                epoch_hex = log["topics"][1]
                epoch_num = int(epoch_hex, 16)
                
                # Topic 2 appears to be user address
                user_address = "0x" + log["topics"][2][-40:]
                
                epoch_data.append({
                    "epoch": epoch_num,
                    "user": user_address,
                    "block": int(log["blockNumber"], 16),
                    "tx": log["transactionHash"]
                })
                
                print(f"Epoch {epoch_num}: User {user_address}")
        
        return epoch_data
        
    except Exception as e:
        print(f"Failed to decode epoch events: {e}")
        return []

def create_provider_name_mapping(providers_data: List[Dict]):
    """Create a mapping from addresses to provider names (placeholder)"""
    print(f"\n=== Provider Name Mapping ===")
    
    # For now, we'll use shortened addresses as names
    # In a real implementation, you'd need an external service or database
    # to map addresses to human-readable names
    
    name_mapping = {}
    for i, provider in enumerate(providers_data[:10]):
        address = provider["address"]
        # Create a short name from the address
        short_name = f"Provider_{address[:6]}...{address[-4:]}"
        name_mapping[address] = short_name
        print(f"{address} -> {short_name}")
    
    return name_mapping

def simulate_target_output(providers_data: List[Dict], name_mapping: Dict[str, str]):
    """Create output in the same format as your current scraping"""
    print(f"\n=== Target Output Format ===")
    
    total_vote_power = sum(p["vote_power"] for p in providers_data)
    
    target_data = {
        "timestamp": "2025-07-21T15-30-00Z",  # Would be current time
        "network": "flare",
        "providers": []
    }
    
    # Sort by vote power and calculate percentages
    sorted_providers = sorted(providers_data, key=lambda x: x["vote_power"], reverse=True)
    
    for provider in sorted_providers[:10]:  # Top 10
        address = provider["address"]
        percentage = (provider["vote_power"] / total_vote_power) * 100 if total_vote_power > 0 else 0
        
        target_data["providers"].append({
            "name": name_mapping.get(address, address),
            "vote_power": round(percentage, 2)
        })
    
    print(json.dumps(target_data, indent=2))
    return target_data

def main():
    """Main decoding function"""
    print("Decoding Flare Network Vote Power Data")
    print("=" * 50)
    
    # Decode vote power events
    providers_data = decode_vote_power_events()
    
    # Decode epoch events
    epoch_data = decode_epoch_events()
    
    if providers_data:
        # Create name mapping
        name_mapping = create_provider_name_mapping(providers_data)
        
        # Generate target output
        target_output = simulate_target_output(providers_data, name_mapping)
        
        print(f"\n" + "=" * 50)
        print("SUCCESS! We can extract vote power data from the blockchain!")
        print("Next steps:")
        print("1. Implement proper provider name resolution")
        print("2. Handle historical epoch queries")
        print("3. Replace the scraping logic in current_vote_power.py")
    else:
        print("Need to investigate further to find vote power data")

if __name__ == "__main__":
    main()
