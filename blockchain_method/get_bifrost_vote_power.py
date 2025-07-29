#!/usr/bin/env python3
"""
Extract raw vote power values for specific FTSO providers like Bifrost Wallet.
Focus on getting the actual numbers, not percentages.
"""

from flare_rpc_new import make_rpc_call, FlareRPCError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_bifrost_vote_power(network: str = "flare"):
    """
    Get the current vote power for Bifrost Wallet specifically.
    
    From the screenshot:
    - Reward Epoch: 313
    - Bifrost vote power: 1,683,080,166
    """
    
    # Bifrost Wallet address from our analysis
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    
    logger.info(f"Getting vote power for Bifrost Wallet ({bifrost_address}) on {network}")
    
    try:
        # Try different approaches to get vote power
        
        # Approach 1: Check VotePowerContract directly for current vote power
        vote_power_contract = "0x1000000000000000000000000000000000000002"
        
        # Try votePowerOf(address) function - common pattern
        # Function signature: votePowerOf(address) - 0x142d1018
        vote_power_data = f"0x142d1018{bifrost_address[2:].zfill(64)}"
        
        result = make_rpc_call(
            network,
            "eth_call",
            [{
                "to": vote_power_contract,
                "data": vote_power_data
            }, "latest"]
        )
        
        if result and result != "0x":
            vote_power = int(result, 16)
            logger.info(f"✅ Bifrost vote power (votePowerOf): {vote_power:,}")
            return vote_power
        
        # Approach 2: Try votePowerOfAt(address, blockNumber) 
        # Get current block first
        current_block_result = make_rpc_call(network, "eth_blockNumber", [])
        current_block = int(current_block_result, 16)
        
        # Function signature: votePowerOfAt(address,uint256) - 0x92bfe6a8
        vote_power_at_data = f"0x92bfe6a8{bifrost_address[2:].zfill(64)}{current_block:064x}"
        
        result = make_rpc_call(
            network,
            "eth_call",
            [{
                "to": vote_power_contract,
                "data": vote_power_at_data
            }, "latest"]
        )
        
        if result and result != "0x":
            vote_power = int(result, 16)
            logger.info(f"✅ Bifrost vote power (votePowerOfAt): {vote_power:,}")
            return vote_power
            
        # Approach 3: Try balanceOf(address) - ERC20 pattern
        # Function signature: balanceOf(address) - 0x70a08231
        balance_data = f"0x70a08231{bifrost_address[2:].zfill(64)}"
        
        result = make_rpc_call(
            network,
            "eth_call",
            [{
                "to": vote_power_contract,
                "data": balance_data
            }, "latest"]
        )
        
        if result and result != "0x":
            balance = int(result, 16)
            logger.info(f"✅ Bifrost balance: {balance:,}")
            return balance
            
        logger.warning("❌ No vote power found with standard functions")
        return None
        
    except Exception as e:
        logger.error(f"Error getting Bifrost vote power: {e}")
        return None

def get_vote_power_from_events(network: str = "flare"):
    """
    Extract vote power from recent events for all providers.
    Focus on getting the raw numbers.
    """
    
    vote_power_contract = "0x1000000000000000000000000000000000000002"
    vote_power_event_sig = "0xe7aa66356adbd5e839ef210626f6d8f6f72109c17fadf4c4f9ca82b315ae79b4"
    
    # Bifrost address for verification
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    
    try:
        # Get current block
        current_block_result = make_rpc_call(network, "eth_blockNumber", [])
        current_block = int(current_block_result, 16)
        
        # Look in recent blocks
        from_block = hex(current_block - 500)  # Smaller range for focus
        
        logger.info(f"Searching for vote power events from block {from_block} to latest")
        
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
            logger.warning("No vote power events found")
            return None
        
        logger.info(f"Found {len(events_result)} vote power events")
        
        # Look specifically for Bifrost
        bifrost_vote_power = None
        all_providers = {}
        
        for i, event in enumerate(events_result[-10:]):  # Look at last 10 events
            try:
                data = event["data"]
                if len(data) >= 130:
                    # Extract address and vote power
                    provider_hex = data[2 + 24:2 + 64]
                    provider_address = "0x" + provider_hex
                    
                    vote_power_hex = data[66:130]
                    vote_power = int(vote_power_hex, 16)
                    
                    all_providers[provider_address] = vote_power
                    
                    if provider_address.lower() == bifrost_address.lower():
                        bifrost_vote_power = vote_power
                        logger.info(f"🎯 Found Bifrost in event {i}: {vote_power:,}")
                    
                    # Also show other providers for context
                    logger.info(f"Event {i}: {provider_address} = {vote_power:,}")
                    
            except Exception as e:
                logger.debug(f"Error processing event {i}: {e}")
        
        if bifrost_vote_power:
            logger.info(f"✅ Bifrost Wallet vote power from events: {bifrost_vote_power:,}")
            logger.info(f"   Target from screenshot: 1,683,080,166")
            return bifrost_vote_power
        else:
            logger.warning(f"❌ Bifrost address {bifrost_address} not found in recent events")
            return None
            
    except Exception as e:
        logger.error(f"Error getting vote power from events: {e}")
        return None

def main():
    print("🔍 Getting Bifrost Wallet Vote Power")
    print("=" * 50)
    print("Target: 1,683,080,166 (from Flare FTSO Statistics)")
    print("=" * 50)
    
    # Try direct function calls first
    logger.info("Approach 1: Direct contract function calls")
    vote_power = get_bifrost_vote_power("flare")
    
    if vote_power:
        print(f"✅ Direct call result: {vote_power:,}")
        if vote_power == 1683080166:
            print("🎯 EXACT MATCH with screenshot!")
        else:
            print(f"📊 Difference: {abs(vote_power - 1683080166):,}")
    else:
        print("❌ Direct calls failed")
    
    print("\n" + "=" * 50)
    
    # Try events approach
    logger.info("Approach 2: Vote power events")
    event_vote_power = get_vote_power_from_events("flare")
    
    if event_vote_power:
        print(f"✅ Event result: {event_vote_power:,}")
        if event_vote_power == 1683080166:
            print("🎯 EXACT MATCH with screenshot!")
        else:
            print(f"📊 Difference: {abs(event_vote_power - 1683080166):,}")
    else:
        print("❌ Events approach failed")

if __name__ == "__main__":
    main()
