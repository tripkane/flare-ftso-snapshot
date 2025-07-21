import requests
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# Flare RPC configuration
ANKR_API_KEY = os.getenv("ANKR_API_KEY", "0eb7f4b8bae149b70576678cbe1b2d892a1edb981112e5005c054391f384ed9a")
FLARE_RPC_URL = f"https://rpc.ankr.com/flare/{ANKR_API_KEY}"
SONGBIRD_RPC_URL = f"https://rpc.ankr.com/flare_songbird/{ANKR_API_KEY}"  # Correct Songbird endpoint

# Known Flare system contracts
FLARE_CONTRACTS = {
    "flare": {
        "VotePowerContract": "0x1000000000000000000000000000000000000002",
        "EpochContract": "0xdbf71d7840934eb82fa10173103d4e9fd4054dd1",
    },
    "songbird": {
        "VotePowerContract": "0x1000000000000000000000000000000000000002", 
        "EpochContract": "0xdbf71d7840934eb82fa10173103d4e9fd4054dd1",
    }
}

# Event signatures
VOTE_POWER_EVENT = "0xe7aa66356adbd5e839ef210626f6d8f6f72109c17fadf4c4f9ca82b315ae79b4"
EPOCH_EVENT = "0x63db91b14b3d088c677f046180aefcea7a236649704d90ce810cde455d38d936"

class FlareRPCError(Exception):
    """Custom exception for RPC-related errors"""
    pass

def make_rpc_call(method: str, params: List[Any] = None, network: str = "flare") -> Dict[Any, Any]:
    """Make a JSON-RPC call to the Flare network via Ankr"""
    if params is None:
        params = []
    
    # Choose RPC URL based on network
    rpc_url = FLARE_RPC_URL if network == "flare" else SONGBIRD_RPC_URL
    
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    try:
        response = requests.post(rpc_url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            raise FlareRPCError(f"RPC Error: {result['error']}")
        
        return result
    except requests.RequestException as e:
        raise FlareRPCError(f"Network error: {e}")

def get_latest_block(network: str = "flare") -> int:
    """Get the latest block number"""
    result = make_rpc_call("eth_blockNumber", network=network)
    return int(result["result"], 16)

def get_vote_power_events(from_block: int = None, to_block: str = "latest", network: str = "flare") -> List[Dict]:
    """Get vote power events from the blockchain"""
    if from_block is None:
        # Default to recent blocks if no specific block is provided
        latest = get_latest_block(network)
        from_block = latest - 100
    
    try:
        result = make_rpc_call("eth_getLogs", [{
            "address": FLARE_CONTRACTS[network]["VotePowerContract"],
            "topics": [VOTE_POWER_EVENT],
            "fromBlock": hex(from_block),
            "toBlock": to_block
        }], network=network)
        
        return result["result"]
    except Exception as e:
        raise FlareRPCError(f"Failed to get vote power events: {e}")

def decode_vote_power_event(log: Dict) -> Dict[str, Any]:
    """Decode a single vote power event log"""
    try:
        data = log["data"]
        if len(data) != 130:  # 0x + 128 hex chars = 2 * 32-byte values
            raise ValueError(f"Invalid data length: {len(data)}")
        
        # Extract address (first 32 bytes, but address is in last 20 bytes)
        address_hex = data[26:66]  # Skip 0x and padding, get 40 chars
        address = "0x" + address_hex
        
        # Extract vote power (second 32 bytes)
        vote_power_hex = data[66:130]
        vote_power = int(vote_power_hex, 16)
        
        return {
            "address": address,
            "vote_power": vote_power,
            "block_number": int(log["blockNumber"], 16),
            "transaction_hash": log["transactionHash"],
            "log_index": int(log["logIndex"], 16)
        }
    except Exception as e:
        raise FlareRPCError(f"Failed to decode vote power event: {e}")

def get_current_vote_power_data(network: str = "flare") -> List[Dict[str, Any]]:
    """Get current vote power data for all providers"""
    try:
        # Get recent vote power events
        logs = get_vote_power_events(network=network)
        
        if not logs:
            raise FlareRPCError("No vote power events found")
        
        # Group by transaction to get the most recent complete set
        tx_groups = {}
        for log in logs:
            tx_hash = log["transactionHash"]
            if tx_hash not in tx_groups:
                tx_groups[tx_hash] = []
            tx_groups[tx_hash].append(log)
        
        # Get the most recent transaction (highest block number)
        latest_tx = max(tx_groups.keys(), key=lambda tx: max(int(log["blockNumber"], 16) for log in tx_groups[tx]))
        latest_logs = tx_groups[latest_tx]
        
        # Decode all events from the latest transaction
        providers = []
        for log in latest_logs:
            try:
                decoded = decode_vote_power_event(log)
                providers.append(decoded)
            except Exception as e:
                print(f"Warning: Failed to decode log {log['logIndex']}: {e}")
                continue
        
        # Remove duplicates and keep highest vote power per address
        unique_providers = {}
        for provider in providers:
            address = provider["address"]
            if address not in unique_providers or provider["vote_power"] > unique_providers[address]["vote_power"]:
                unique_providers[address] = provider
        
        return list(unique_providers.values())
        
    except Exception as e:
        raise FlareRPCError(f"Failed to get current vote power data: {e}")

def calculate_vote_power_percentages(providers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate vote power percentages from raw vote power amounts"""
    total_vote_power = sum(p["vote_power"] for p in providers)
    
    if total_vote_power == 0:
        return []
    
    results = []
    for provider in providers:
        percentage = (provider["vote_power"] / total_vote_power) * 100
        results.append({
            "address": provider["address"],
            "vote_power": provider["vote_power"],
            "vote_power_pct": round(percentage, 2),
            "block_number": provider["block_number"],
            "transaction_hash": provider["transaction_hash"]
        })
    
    # Sort by percentage descending
    return sorted(results, key=lambda x: x["vote_power_pct"], reverse=True)

def get_provider_name(address: str) -> str:
    """Get human-readable name for a provider address"""
    # TODO: Implement proper provider name resolution
    # This could query a database, external API, or predefined mapping
    
    # Known provider addresses (placeholder - expand as needed)
    known_providers = {
        "0xdbf71d7840934eb82fa10173103d4e9fd4054dd1": "Provider_DBF7",
        "0x9c7a4c83842b29bb4a082b0e689cb9474bd938d0": "Provider_9C7A",
        "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c": "Provider_4D92",
        "0x7b61f9f27153a4f2f57dc30bf08a8eb0ccb96c22": "Provider_7B61",
        "0xbce1972de5d1598a948a36186ecebfd4690f3a5c": "Provider_BCE1",
        "0x89e50dc0380e597ece79c8494baafd84537ad0d4": "Provider_89E5",
    }
    
    return known_providers.get(address, f"Provider_{address[:6]}...{address[-4:]}")

def fetch_flare_providers_rpc(network: str = "flare") -> List[Dict[str, Any]]:
    """
    Main function to fetch provider data via RPC - replacement for scrape_flaremetrics()
    Returns data in the same format as the original scraping function
    """
    try:
        # Get current vote power data from blockchain
        providers_data = get_current_vote_power_data(network)
        
        if not providers_data:
            return []
        
        # Calculate percentages
        providers_with_pct = calculate_vote_power_percentages(providers_data)
        
        # Format data to match scraping output
        formatted_providers = []
        for provider in providers_with_pct:
            formatted_providers.append({
                "name": get_provider_name(provider["address"]),
                "address": provider["address"],
                "vote_power_pct": provider["vote_power_pct"],
                "vote_power": provider["vote_power"],
                "block_number": provider["block_number"]
            })
        
        return formatted_providers
        
    except Exception as e:
        raise FlareRPCError(f"Failed to fetch provider data for {network}: {e}")

def get_historical_vote_power(epoch_number: int, network: str = "flare") -> List[Dict[str, Any]]:
    """Get historical vote power data for a specific epoch"""
    # TODO: Implement historical epoch queries
    # This would require:
    # 1. Map epoch numbers to block ranges
    # 2. Query vote power events for that block range
    # 3. Return data in the same format as current data
    
    raise NotImplementedError("Historical epoch queries not yet implemented")

def test_rpc_connection(network: str = "flare") -> bool:
    """Test RPC connection and basic functionality"""
    try:
        latest_block = get_latest_block(network)
        print(f"✓ RPC connection successful for {network}")
        print(f"✓ Latest block: {latest_block}")
        return True
    except Exception as e:
        print(f"✗ RPC connection failed for {network}: {e}")
        return False

if __name__ == "__main__":
    # Test the RPC functionality
    print("Testing Flare RPC Module")
    print("=" * 40)
    
    # Test connection
    if test_rpc_connection("flare"):
        try:
            # Test fetching provider data
            providers = fetch_flare_providers_rpc("flare")
            print(f"\n✓ Successfully fetched {len(providers)} providers")
            
            # Show top 5 providers
            print("\nTop 5 providers:")
            for i, provider in enumerate(providers[:5]):
                print(f"  {i+1}. {provider['name']}: {provider['vote_power_pct']}%")
                
        except Exception as e:
            print(f"✗ Failed to fetch provider data: {e}")
