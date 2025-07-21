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

def investigate_active_contract(address: str, max_logs: int = 10):
    """Investigate what a specific contract does by examining its logs"""
    print(f"\n=== Investigating Contract {address} ===")
    
    try:
        # Get recent logs for this contract
        result = make_rpc_call("eth_getLogs", [{
            "address": address,
            "fromBlock": hex(44880900),
            "toBlock": "latest"
        }])
        
        logs = result["result"][:max_logs]  # Limit for analysis
        print(f"Found {len(logs)} recent logs")
        
        if logs:
            print(f"Sample log structure:")
            sample_log = logs[0]
            print(f"  Topics: {len(sample_log['topics'])} items")
            print(f"  Data length: {len(sample_log['data'])} chars")
            print(f"  First topic: {sample_log['topics'][0] if sample_log['topics'] else 'None'}")
            
            # Look for patterns in the topics (event signatures)
            topic_patterns = {}
            for log in logs:
                if log['topics']:
                    first_topic = log['topics'][0]
                    topic_patterns[first_topic] = topic_patterns.get(first_topic, 0) + 1
            
            print(f"Event signature patterns:")
            for topic, count in topic_patterns.items():
                print(f"    {topic}: {count} occurrences")
        
        return logs
    except Exception as e:
        print(f"Failed to investigate contract: {e}")
        return []

def decode_potential_vote_power_data(logs: List[Dict]):
    """Try to decode data that might contain vote power information"""
    print(f"\n=== Analyzing Potential Vote Power Data ===")
    
    for i, log in enumerate(logs[:5]):  # Analyze first 5 logs
        print(f"\nLog {i + 1}:")
        print(f"  Transaction: {log['transactionHash']}")
        print(f"  Topics: {log['topics']}")
        print(f"  Data: {log['data']}")
        
        # Try to decode numeric data
        if log['data'] and log['data'] != '0x':
            try:
                # Remove '0x' prefix and convert hex to int
                hex_data = log['data'][2:]
                if len(hex_data) == 64:  # Standard 256-bit value
                    value = int(hex_data, 16)
                    print(f"  Decoded as integer: {value}")
                    
                    # Check if this could be a percentage (0-100)
                    if 0 <= value <= 100:
                        print(f"    -> Could be percentage: {value}%")
                    # Check if this could be a large vote power amount
                    elif value > 1000000:
                        print(f"    -> Could be vote power amount: {value:,}")
            except:
                pass
        
        # Analyze topics for addresses (potential voter addresses)
        for j, topic in enumerate(log['topics']):
            if topic.startswith('0x000000000000000000000000') and len(topic) == 66:
                # This looks like a padded address
                potential_address = '0x' + topic[-40:]
                print(f"  Topic {j} potential address: {potential_address}")

def find_system_contracts():
    """Look for known Flare system contracts"""
    print(f"\n=== Known Flare System Contracts ===")
    
    # Common Flare system contract addresses (these are more likely to be correct)
    known_addresses = [
        "0x1000000000000000000000000000000000000001",  # Genesis contract
        "0x1000000000000000000000000000000000000002",  # Most active from our scan
        "0x1000000000000000000000000000000000000003",  # Potential system contract
        "0x1000000000000000000000000000000000000004",  # Potential system contract
        "0x1000000000000000000000000000000000000005",  # Potential system contract
    ]
    
    for address in known_addresses:
        try:
            result = make_rpc_call("eth_getCode", [address, "latest"])
            code = result["result"]
            has_code = code != "0x" and len(code) > 2
            print(f"  {address}: {'✓ Has contract code' if has_code else '✗ No code'}")
        except:
            print(f"  {address}: ✗ Error checking")

def main():
    """Main investigation function"""
    print("Deep Dive: Flare Network Contract Investigation")
    print("=" * 60)
    
    # Investigate the most active contracts we found
    most_active_contracts = [
        "0x1000000000000000000000000000000000000002",  # 384 events
        "0x5646f8f757ed7238f28ae930ab7e1d806413df36",  # 268 events  
        "0xdbf71d7840934eb82fa10173103d4e9fd4054dd1",  # 101 events
    ]
    
    # Check system contracts
    find_system_contracts()
    
    # Investigate each active contract
    for address in most_active_contracts:
        logs = investigate_active_contract(address)
        if logs:
            decode_potential_vote_power_data(logs)
    
    print("\n" + "=" * 60)
    print("Key Findings Summary:")
    print("1. Identify which contracts contain vote power data")
    print("2. Understand the event structure and data encoding") 
    print("3. Map contract addresses to provider names")
    print("4. Calculate total vote power and percentages")

if __name__ == "__main__":
    main()
