#!/usr/bin/env python3
"""
Extract FTSO vote power data from VotePower events on contract 0x1000000000000000000000000000000000000002
"""

from flare_rpc_new import make_rpc_call, get_provider_name
import json

def get_vote_power_from_events(network="flare", block_count=100):
    """Get vote power data by analyzing VotePower events"""
    
    vote_power_contract = "0x1000000000000000000000000000000000000002"
    vote_power_event = "0xe7aa66356adbd5e839ef210626f6d8f6f72109c17fadf4c4f9ca82b315ae79b4"
    
    try:
        # Get recent blocks
        latest_result = make_rpc_call(network, "eth_blockNumber", [])
        latest_block = int(latest_result, 16)
        from_block = hex(latest_block - block_count)
        
        print(f"📊 Analyzing VotePower events from block {from_block} to latest...")
        
        # Get VotePower events
        logs_result = make_rpc_call(
            network,
            "eth_getLogs",
            [{
                "address": vote_power_contract,
                "fromBlock": from_block,
                "toBlock": "latest",
                "topics": [vote_power_event]
            }]
        )
        
        if not logs_result:
            print("❌ No VotePower events found")
            return []
            
        print(f"✅ Found {len(logs_result)} VotePower events")
        
        # Extract provider data from events
        providers = {}
        
        for log in logs_result:
            try:
                # Event data structure: address (32 bytes) + vote_power (32 bytes)
                data = log['data']
                if len(data) >= 130:  # 0x + 128 hex chars (64 bytes)
                    # Extract address (first 32 bytes, take last 20)
                    address_hex = data[2:66]  # Skip 0x, get first 32 bytes
                    provider_address = "0x" + address_hex[-40:]  # Last 20 bytes
                    
                    # Extract vote power (second 32 bytes)
                    vote_power_hex = data[66:130]
                    vote_power = int(vote_power_hex, 16) if vote_power_hex else 0
                    
                    # Store latest vote power for each provider
                    providers[provider_address] = {
                        "address": provider_address,
                        "vote_power": vote_power,
                        "block_number": int(log['blockNumber'], 16),
                        "transaction": log['transactionHash']
                    }
                    
            except Exception as e:
                print(f"⚠️ Error parsing event: {e}")
                continue
        
        # Convert to list and calculate percentages
        provider_list = list(providers.values())
        total_vote_power = sum(p["vote_power"] for p in provider_list)
        
        if total_vote_power > 0:
            for provider in provider_list:
                vote_power_pct = (provider["vote_power"] / total_vote_power) * 100
                provider["vote_power_pct"] = round(vote_power_pct, 4)
                provider["name"] = get_provider_name(provider["address"])
        
        # Sort by vote power
        provider_list.sort(key=lambda x: x["vote_power"], reverse=True)
        
        print(f"\\n📋 Found {len(provider_list)} providers with total vote power: {total_vote_power}")
        
        return provider_list
        
    except Exception as e:
        print(f"❌ Error getting vote power from events: {e}")
        return []

def display_vote_power_results(providers):
    """Display vote power results in a nice format"""
    
    if not providers:
        print("❌ No provider data to display")
        return
    
    print(f"\\n{'='*80}")
    print(f"🏆 FTSO VOTE POWER FROM BLOCKCHAIN EVENTS")
    print(f"{'='*80}")
    print(f"{'Rank':<4} {'Provider Name':<25} {'Address':<42} {'Vote Power %':<12} {'Raw Power'}")
    print(f"{'-'*80}")
    
    for i, provider in enumerate(providers[:20], 1):  # Show top 20
        name = provider.get("name", "Unknown")[:24]
        address = provider["address"]
        vote_power_pct = provider.get("vote_power_pct", 0)
        raw_power = provider["vote_power"]
        
        print(f"{i:<4} {name:<25} {address:<42} {vote_power_pct:<12.2f} {raw_power:,}")
    
    if len(providers) > 20:
        print(f"... and {len(providers) - 20} more providers")
    
    print(f"{'-'*80}")
    
    # Show summary statistics
    total_percentage = sum(p.get("vote_power_pct", 0) for p in providers)
    top_5_percentage = sum(p.get("vote_power_pct", 0) for p in providers[:5])
    
    print(f"📊 Summary:")
    print(f"   Total providers: {len(providers)}")
    print(f"   Total percentage: {total_percentage:.2f}%")
    print(f"   Top 5 providers control: {top_5_percentage:.2f}%")
    
    # Check for providers above 2.5% (FTSO cap)
    over_cap = [p for p in providers if p.get("vote_power_pct", 0) > 2.5]
    if over_cap:
        print(f"   ⚠️ Providers over 2.5% cap: {len(over_cap)}")
        for p in over_cap:
            print(f"      {p.get('name', 'Unknown')}: {p.get('vote_power_pct', 0):.2f}%")

def save_vote_power_data(providers, network="flare"):
    """Save vote power data in the same format as the existing system"""
    
    from current_vote_power_rpc import save_current_vote_power, apply_ftso_vote_power_cap
    import datetime
    
    if not providers:
        print("❌ No data to save")
        return
    
    # Apply FTSO vote power cap
    providers_for_cap = []
    for p in providers:
        providers_for_cap.append({
            "name": p.get("name", "Unknown"),
            "address": p["address"],
            "vote_power_pct": p.get("vote_power_pct", 0),
            "raw_vote_power": p["vote_power"]
        })
    
    capped_providers = apply_ftso_vote_power_cap(providers_for_cap)
    
    # Format for saving
    data = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ"),
        "network": network,
        "data_source": "blockchain_events",
        "providers": [
            {
                "name": p["name"],
                "vote_power": p.get("vote_power_pct", 0.0),
                "capped_vote_power": p.get("capped_vote_power", 0.0),
                "original_vote_power": p.get("original_vote_power_pct", 0.0),
                "was_capped": p.get("was_capped", False)
            }
            for p in capped_providers
        ],
    }
    
    save_current_vote_power(data, network)
    print(f"✅ Saved vote power data for {len(capped_providers)} providers")

def main():
    """Main function to extract and display vote power from events"""
    
    print("🔍 EXTRACTING FTSO VOTE POWER FROM BLOCKCHAIN EVENTS")
    print("=" * 60)
    
    # Get data from Flare network
    providers = get_vote_power_from_events("flare", 1000)  # Look at more blocks
    
    if providers:
        display_vote_power_results(providers)
        
        # Ask user if they want to save the data
        response = input(f"\\n💾 Save this data? (y/N): ").strip().lower()
        if response in ('y', 'yes'):
            save_vote_power_data(providers, "flare")
        else:
            print("📋 Data not saved")
    else:
        print("❌ No vote power data found")

if __name__ == "__main__":
    main()
