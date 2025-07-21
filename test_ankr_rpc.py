import requests
import json
import os
from typing import Dict, List, Any, Optional

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

def test_basic_connectivity():
    """Test basic RPC connectivity"""
    print("=== Testing Basic Connectivity ===")
    try:
        result = make_rpc_call("eth_blockNumber")
        block_number = int(result["result"], 16)
        print(f"✓ Connected successfully")
        print(f"✓ Latest block: {block_number}")
        return block_number
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return None

def get_block_info(block_number: int):
    """Get detailed block information"""
    print(f"\n=== Block {block_number} Information ===")
    try:
        result = make_rpc_call("eth_getBlockByNumber", [hex(block_number), False])
        block = result["result"]
        if block:
            print(f"✓ Block hash: {block['hash']}")
            print(f"✓ Timestamp: {int(block['timestamp'], 16)}")
            print(f"✓ Transaction count: {len(block['transactions'])}")
        return block
    except Exception as e:
        print(f"✗ Failed to get block info: {e}")
        return None

def explore_contract_addresses():
    """Try to find known Flare contract addresses"""
    print("\n=== Known Flare Contract Addresses ===")
    # These are potential FSP contract addresses - need to verify
    potential_contracts = {
        "VoterRegistry": "0x0000000000000000000000000000000000000000",  # Placeholder
        "FlareSystemsManager": "0x0000000000000000000000000000000000000000",  # Placeholder
        "VoterWhitelister": "0x0000000000000000000000000000000000000000",  # Placeholder
    }
    
    print("Note: Need to find actual contract addresses for FSP contracts")
    for name, address in potential_contracts.items():
        print(f"  {name}: {address}")

def test_contract_call(contract_address: str, method_signature: str):
    """Test calling a contract method"""
    print(f"\n=== Testing Contract Call ===")
    print(f"Contract: {contract_address}")
    print(f"Method: {method_signature}")
    
    try:
        # This is a placeholder - we need actual contract addresses and method signatures
        result = make_rpc_call("eth_call", [
            {
                "to": contract_address,
                "data": method_signature
            },
            "latest"
        ])
        print(f"✓ Contract call successful")
        print(f"✓ Result: {result['result']}")
        return result["result"]
    except Exception as e:
        print(f"✗ Contract call failed: {e}")
        return None

def explore_transaction_logs(block_range: int = 100):
    """Look for FSP-related events in recent blocks"""
    print(f"\n=== Exploring Recent Transaction Logs ===")
    try:
        # Get logs for FSP-related events
        # This is a placeholder - we need actual contract addresses and event signatures
        result = make_rpc_call("eth_getLogs", [{
            "fromBlock": "latest",
            "toBlock": "latest",
            # "address": ["0xContractAddress1", "0xContractAddress2"],
            # "topics": [["0xEventSignature1", "0xEventSignature2"]]
        }])
        
        logs = result["result"]
        print(f"✓ Found {len(logs)} logs in latest block")
        
        if logs:
            print("Sample log:")
            print(json.dumps(logs[0], indent=2))
        
        return logs
    except Exception as e:
        print(f"✗ Failed to get logs: {e}")
        return []

def main():
    """Main test function"""
    print("Testing Ankr RPC Connection to Flare Network")
    print("=" * 50)
    
    # Test basic connectivity
    latest_block = test_basic_connectivity()
    if not latest_block:
        return
    
    # Get block information
    get_block_info(latest_block)
    
    # Explore contract addresses
    explore_contract_addresses()
    
    # Explore transaction logs
    explore_transaction_logs()
    
    print("\n" + "=" * 50)
    print("Next Steps:")
    print("1. Find actual FSP contract addresses")
    print("2. Identify contract methods for vote power data")
    print("3. Map provider addresses to names")
    print("4. Calculate vote power percentages")

if __name__ == "__main__":
    main()
