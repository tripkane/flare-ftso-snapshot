#!/usr/bin/env python3
"""
Debug vote power extraction - check units, totals, and epoch information
"""

from flare_rpc_new import make_rpc_call, FlareRPCError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_vote_power_scale(network: str = "flare"):
    """
    Analyze the scale and units of vote power data to understand the discrepancy.
    
    From screenshot:
    - Total Weight: 65,490
    - Vote Power Block: 44,798,407  
    - Bifrost: 1,683,080,166
    """
    
    vote_power_contract = "0x1000000000000000000000000000000000000002"
    vote_power_event_sig = "0xe7aa66356adbd5e839ef210626f6d8f6f72109c17fadf4c4f9ca82b315ae79b4"
    
    try:
        # Get current block
        current_block_result = make_rpc_call(network, "eth_blockNumber", [])
        current_block = int(current_block_result, 16)
        
        logger.info(f"Current block: {current_block:,}")
        
        # Look at more recent events to get full picture
        from_block = hex(current_block - 100)  # Very recent
        
        events_result = make_rpc_call(
            network,
            "eth_getLogs",
            [{
                "address": vote_power_contract,
                "topics": [vote_power_event_sig],
                "fromBlock": from_block,
                "toBlock": "latest"
            }]
        )
        
        if not events_result:
            logger.warning("No events found")
            return
            
        logger.info(f"Found {len(events_result)} recent events")
        
        # Aggregate by provider to get totals
        provider_totals = {}
        provider_names = {
            "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c": "Bifrost Wallet",
            "0x7b61f9f27153a4f2f57dc30bf08a8eb0ccb96c22": "Flare.Space", 
            "0xbce1972de5d1598a948a36186ecebfd4690f3a5c": "AlphaOracle",
            "0x9c7a4c83842b29bb4a082b0e689cb9474bd938d0": "Flare Oracle",
            "0x89e50dc0380e597ece79c8494baafd84537ad0d4": "Atlas TSO",
            "0xdbf71d7840934eb82fa10173103d4e9fd4054dd1": "NORTSO",
        }
        
        # Process all events to get latest values
        for event in events_result:
            try:
                data = event["data"]
                if len(data) >= 130:
                    provider_hex = data[2 + 24:2 + 64]
                    provider_address = "0x" + provider_hex
                    
                    vote_power_hex = data[66:130]
                    vote_power = int(vote_power_hex, 16)
                    
                    # Keep latest value for each provider
                    provider_totals[provider_address] = vote_power
                    
            except Exception as e:
                continue
        
        print("\\n🔍 VOTE POWER ANALYSIS")
        print("=" * 60)
        print("From Flare FTSO Statistics Screenshot:")
        print("- Bifrost target: 1,683,080,166")
        print("- Total Weight: 65,490")
        print("- Vote Power Block: 44,798,407")
        print("=" * 60)
        
        total_from_events = 0
        for address, vote_power in provider_totals.items():
            name = provider_names.get(address, address[:10])
            total_from_events += vote_power
            
            print(f"{name:<15}: {vote_power:>15,}")
            
            if address.lower() == "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c":
                ratio = 1683080166 / vote_power if vote_power > 0 else 0
                print(f"{'':15}  Target/Actual: {ratio:,.2f}x")
        
        print("-" * 60)
        print(f"{'TOTAL':<15}: {total_from_events:>15,}")
        
        # Calculate scaling factors
        if total_from_events > 0:
            # Try different interpretations
            print("\\n📊 SCALING ANALYSIS:")
            print(f"Total from events: {total_from_events:,}")
            print(f"Vote Power Block from screenshot: 44,798,407")
            print(f"Scale factor (if events are in wei): {total_from_events / 1e18:,.0f}")
            print(f"Scale factor vs Vote Power Block: {44798407 / total_from_events:,.2f}x")
            
            # Check if Bifrost ratio makes sense
            bifrost_from_events = provider_totals.get("0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c", 0)
            if bifrost_from_events > 0:
                bifrost_scaled = (bifrost_from_events / total_from_events) * 44798407
                print(f"\\nIf we scale Bifrost by Vote Power Block:")
                print(f"Bifrost scaled: {bifrost_scaled:,.0f}")
                print(f"Bifrost target: 1,683,080,166")
                print(f"Still off by: {abs(bifrost_scaled - 1683080166):,.0f}")
        
    except Exception as e:
        logger.error(f"Error in analysis: {e}")

def check_different_event_types():
    """Check if there are other event types that might contain the right data"""
    
    vote_power_contract = "0x1000000000000000000000000000000000000002"
    
    # Common event signatures to try
    event_signatures = {
        "VotePowerChanged": "0xe7aa66356adbd5e839ef210626f6d8f6f72109c17fadf4c4f9ca82b315ae79b4",
        "Delegate": "0x8643c9c6c0ab89b37e04ea8a4da0e8265f1e3558e0d39b7e2c989b44b4b7cd5",
        "Transfer": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        "Approval": "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",
    }
    
    current_block_result = make_rpc_call("flare", "eth_blockNumber", [])
    current_block = int(current_block_result, 16)
    from_block = hex(current_block - 100)
    
    print("\\n🔍 CHECKING OTHER EVENT TYPES")
    print("=" * 50)
    
    for event_name, signature in event_signatures.items():
        try:
            events = make_rpc_call(
                "flare",
                "eth_getLogs",
                [{
                    "address": vote_power_contract,
                    "topics": [signature],
                    "fromBlock": from_block,
                    "toBlock": "latest"
                }]
            )
            
            print(f"{event_name:<20}: {len(events) if events else 0:>6} events")
            
        except Exception as e:
            print(f"{event_name:<20}: ERROR")

def main():
    print("🔍 DEBUGGING VOTE POWER SCALE ISSUE")
    print("=" * 60)
    
    analyze_vote_power_scale("flare")
    check_different_event_types()

if __name__ == "__main__":
    main()
