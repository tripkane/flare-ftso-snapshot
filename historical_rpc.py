import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from flare_rpc_new import (
    make_rpc_call, get_vote_power_events, decode_vote_power_event, 
    calculate_vote_power_percentages, FlareRPCError
)
from provider_names import get_provider_name

def load_epoch_schedule(file_path: str = "flare_epoch_schedule.json") -> List[Dict]:
    """Load the epoch schedule from JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise FileNotFoundError(f"Could not load epoch schedule: {e}")

def get_block_by_timestamp(target_timestamp: int, network: str = "flare") -> int:
    """
    Find the block number closest to a given timestamp
    
    This uses binary search to efficiently find the block
    """
    try:
        # Get current block as upper bound
        latest_result = make_rpc_call("eth_blockNumber", network=network)
        latest_block = int(latest_result["result"], 16)
        
        # Get the latest block info to determine time range
        latest_block_info = make_rpc_call("eth_getBlockByNumber", [hex(latest_block), False], network=network)
        latest_timestamp = int(latest_block_info["result"]["timestamp"], 16)
        
        if target_timestamp > latest_timestamp:
            return latest_block
        
        # Binary search for the target block
        low, high = 0, latest_block
        
        while low <= high:
            mid = (low + high) // 2
            
            try:
                block_info = make_rpc_call("eth_getBlockByNumber", [hex(mid), False], network=network)
                block_timestamp = int(block_info["result"]["timestamp"], 16)
                
                if abs(block_timestamp - target_timestamp) < 60:  # Within 1 minute
                    return mid
                elif block_timestamp < target_timestamp:
                    low = mid + 1
                else:
                    high = mid - 1
                    
            except Exception as e:
                print(f"Warning: Failed to get block {mid}: {e}")
                high = mid - 1
        
        return high
        
    except Exception as e:
        raise FlareRPCError(f"Failed to find block by timestamp: {e}")

def get_epoch_block_range(epoch_info: Dict, network: str = "flare") -> tuple:
    """
    Get the block range for a specific epoch
    
    Returns (start_block, end_block)
    """
    try:
        # Parse epoch timestamps
        start_time_str = epoch_info["Start (UTC)"]
        end_time_str = epoch_info["End (UTC)"]
        
        # Convert to Unix timestamps
        start_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        
        start_timestamp = int(start_dt.replace(tzinfo=timezone.utc).timestamp())
        end_timestamp = int(end_dt.replace(tzinfo=timezone.utc).timestamp())
        
        # Find corresponding blocks
        start_block = get_block_by_timestamp(start_timestamp, network)
        end_block = get_block_by_timestamp(end_timestamp, network)
        
        return start_block, end_block
        
    except Exception as e:
        raise FlareRPCError(f"Failed to get epoch block range: {e}")

def get_historical_vote_power_for_epoch(epoch_number: int, network: str = "flare") -> List[Dict[str, Any]]:
    """
    Get historical vote power data for a specific epoch
    
    Args:
        epoch_number: The epoch number to query
        network: The network ('flare' or 'songbird')
    
    Returns:
        List of provider data with vote power percentages
    """
    try:
        # Load epoch schedule
        epoch_schedule = load_epoch_schedule()
        
        # Find the epoch info
        epoch_info = None
        for epoch in epoch_schedule:
            if epoch["Epoch Number"] == epoch_number:
                epoch_info = epoch
                break
        
        if not epoch_info:
            raise ValueError(f"Epoch {epoch_number} not found in schedule")
        
        print(f"Getting historical data for Epoch {epoch_number}")
        print(f"  Start: {epoch_info['Start (UTC)']}")
        print(f"  End: {epoch_info['End (UTC)']}")
        
        # Get block range for this epoch
        start_block, end_block = get_epoch_block_range(epoch_info, network)
        
        print(f"  Block range: {start_block} to {end_block}")
        
        # Get vote power events for this epoch
        logs = get_vote_power_events(start_block, hex(end_block), network)
        
        if not logs:
            print(f"No vote power events found for epoch {epoch_number}")
            return []
        
        print(f"  Found {len(logs)} vote power events")
        
        # Group by transaction to get complete snapshots
        tx_groups = {}
        for log in logs:
            tx_hash = log["transactionHash"]
            if tx_hash not in tx_groups:
                tx_groups[tx_hash] = []
            tx_groups[tx_hash].append(log)
        
        # Use the last transaction in the epoch (most recent vote power state)
        latest_tx = max(tx_groups.keys(), key=lambda tx: max(int(log["blockNumber"], 16) for log in tx_groups[tx]))
        latest_logs = tx_groups[latest_tx]
        
        print(f"  Using transaction {latest_tx} with {len(latest_logs)} events")
        
        # Decode vote power events
        providers = []
        for log in latest_logs:
            try:
                decoded = decode_vote_power_event(log)
                providers.append(decoded)
            except Exception as e:
                print(f"Warning: Failed to decode log: {e}")
                continue
        
        # Remove duplicates and calculate percentages
        unique_providers = {}
        for provider in providers:
            address = provider["address"]
            if address not in unique_providers or provider["vote_power"] > unique_providers[address]["vote_power"]:
                unique_providers[address] = provider
        
        providers_list = list(unique_providers.values())
        providers_with_pct = calculate_vote_power_percentages(providers_list)
        
        # Format for output
        formatted_providers = []
        for provider in providers_with_pct:
            formatted_providers.append({
                "name": get_provider_name(provider["address"]),
                "address": provider["address"],
                "vote_power_pct": provider["vote_power_pct"],
                "vote_power": provider["vote_power"],
                "block_number": provider["block_number"]
            })
        
        print(f"  Successfully processed {len(formatted_providers)} providers")
        return formatted_providers
        
    except Exception as e:
        raise FlareRPCError(f"Failed to get historical vote power for epoch {epoch_number}: {e}")

def save_historical_snapshot(epoch_number: int, providers: List[Dict], network: str = "flare"):
    """Save historical snapshot data"""
    try:
        # Load epoch schedule to get timestamp
        epoch_schedule = load_epoch_schedule()
        epoch_info = None
        for epoch in epoch_schedule:
            if epoch["Epoch Number"] == epoch_number:
                epoch_info = epoch
                break
        
        if not epoch_info:
            raise ValueError(f"Epoch {epoch_number} not found")
        
        # Create snapshot data
        snapshot_data = {
            "timestamp": epoch_info["Start (UTC)"].replace(" ", "T").replace(":", "-") + "Z",
            "network": network,
            "epoch": epoch_number,
            "providers": [
                {
                    "name": p["name"],
                    "vote_power": p["vote_power_pct"]
                }
                for p in providers
            ]
        }
        
        # Save to historical snapshots directory
        hist_dir = os.path.join("historical_snapshots", network)
        os.makedirs(hist_dir, exist_ok=True)
        
        filename = f"epoch_{epoch_number}_{network}_snapshot.json"
        filepath = os.path.join(hist_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
        print(f"Saved historical snapshot: {filepath}")
        
        # Also save to docs for web display
        docs_hist_dir = os.path.join("docs", "historical_snapshots", network)
        os.makedirs(docs_hist_dir, exist_ok=True)
        
        with open(os.path.join(docs_hist_dir, filename), 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
    except Exception as e:
        print(f"Failed to save historical snapshot: {e}")

def collect_all_historical_data(network: str = "flare", start_epoch: int = 1, end_epoch: int = None):
    """
    Collect historical data for all epochs
    
    Args:
        network: Network to collect for ('flare' or 'songbird')
        start_epoch: Starting epoch number
        end_epoch: Ending epoch number (None for all available)
    """
    try:
        epoch_schedule = load_epoch_schedule()
        
        if end_epoch is None:
            end_epoch = max(epoch["Epoch Number"] for epoch in epoch_schedule)
        
        print(f"Collecting historical data for {network}")
        print(f"Epoch range: {start_epoch} to {end_epoch}")
        print("=" * 50)
        
        successful = 0
        failed = 0
        
        for epoch_num in range(start_epoch, end_epoch + 1):
            try:
                print(f"\nProcessing Epoch {epoch_num}...")
                providers = get_historical_vote_power_for_epoch(epoch_num, network)
                
                if providers:
                    save_historical_snapshot(epoch_num, providers, network)
                    successful += 1
                    print(f"✓ Epoch {epoch_num} completed")
                else:
                    print(f"✗ No data found for Epoch {epoch_num}")
                    failed += 1
                
            except Exception as e:
                print(f"✗ Failed to process Epoch {epoch_num}: {e}")
                failed += 1
                continue
        
        print("\n" + "=" * 50)
        print(f"Historical data collection completed")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
    except Exception as e:
        print(f"Failed to collect historical data: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python historical_rpc.py <epoch_number>          # Single epoch")
        print("  python historical_rpc.py <start> <end>           # Range of epochs")
        print("  python historical_rpc.py all                     # All epochs")
        sys.exit(1)
    
    network = "flare"  # Default to flare
    
    if sys.argv[1] == "all":
        collect_all_historical_data(network)
    elif len(sys.argv) == 2:
        # Single epoch
        epoch_num = int(sys.argv[1])
        providers = get_historical_vote_power_for_epoch(epoch_num, network)
        if providers:
            save_historical_snapshot(epoch_num, providers, network)
            print(f"\nTop 5 providers for Epoch {epoch_num}:")
            for i, provider in enumerate(providers[:5]):
                print(f"  {i+1}. {provider['name']}: {provider['vote_power_pct']}%")
    elif len(sys.argv) == 3:
        # Range of epochs
        start_epoch = int(sys.argv[1])
        end_epoch = int(sys.argv[2])
        collect_all_historical_data(network, start_epoch, end_epoch)
    else:
        print("Invalid arguments")
        sys.exit(1)
