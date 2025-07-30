#!/usr/bin/env python3
"""
Alternative approach: Find FTSO vote power data using event logs and known patterns
"""

from flare_rpc_new import make_rpc_call
import json

def get_recent_blocks_with_events(network="flare", block_count=100):
    """Get recent blocks and look for FTSO-related events"""
    
    try:
        # Get latest block number
        latest_result = make_rpc_call(network, "eth_blockNumber", [])
        latest_block = int(latest_result, 16)
        
        print(f"Latest block: {latest_block}")
        
        # Look for events in recent blocks
        from_block = hex(latest_block - block_count)
        to_block = "latest"
        
        # Common FTSO event signatures
        event_topics = [
            "0xe7aa66356adbd5e839ef210626f6d8f6f72109c17fadf4c4f9ca82b315ae79b4",  # VotePower related
            "0x63db91b14b3d088c677f046180aefcea7a236649704d90ce810cde455d38d936",  # Epoch related
            "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",  # Approval (common)
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # Transfer (common)
        ]
        
        print(f"\\nSearching for events from block {from_block} to {to_block}...")
        
        for i, topic in enumerate(event_topics):
            try:
                logs_result = make_rpc_call(
                    network,
                    "eth_getLogs",
                    [{
                        "fromBlock": from_block,
                        "toBlock": to_block,
                        "topics": [topic]
                    }]
                )
                
                if logs_result and len(logs_result) > 0:
                    print(f"✅ Topic {i+1}: Found {len(logs_result)} events")
                    
                    # Show first few contract addresses that emit these events
                    unique_addresses = set()
                    for log in logs_result[:20]:  # Check first 20 events
                        if 'address' in log:
                            unique_addresses.add(log['address'])
                    
                    print(f"   Contract addresses: {list(unique_addresses)[:5]}")
                    
                else:
                    print(f"⚪ Topic {i+1}: No events found")
                    
            except Exception as e:
                print(f"❌ Topic {i+1}: Error - {str(e)[:50]}")
    
    except Exception as e:
        print(f"Error getting recent blocks: {e}")

def try_known_ftso_addresses():
    """Try known FTSO-related addresses from various sources"""
    network = "flare"
    
    # These are potential FTSO addresses from various sources
    potential_addresses = [
        "0x1000000000000000000000000000000000000007",  # System contract
        "0x1000000000000000000000000000000000000008", 
        "0x1000000000000000000000000000000000000009",
        "0x100000000000000000000000000000000000000a",
        "0x2d40EB2EB6A6Ba40cE30d4d2D06F69de6EbAE4e8",  # Common Flare address pattern
        "0xbe653c54df337f13fcb726101388f4a4803049f3",  # From your previous discovery
        "0x3d40EB2EB6A6Ba40cE30d4d2D06F69de6EbAE4e8",
        "0x4d40EB2EB6A6Ba40cE30d4d2D06F69de6EbAE4e8",
    ]
    
    print(f"\\n🔍 Testing known potential FTSO addresses...")
    
    for address in potential_addresses:
        try:
            # Check if contract exists
            code_result = make_rpc_call(network, "eth_getCode", [address, "latest"])
            
            if code_result and code_result != "0x":
                print(f"\\n✅ Contract found at {address} (code: {len(code_result)} chars)")
                
                # Try to call getRegisteredVoters() - VoterRegistry function
                # getRegisteredVoters(uint24) - trying with epoch 0
                try:
                    voter_data = "0x2db09808" + "0" * 56  # epoch 0, padded to 32 bytes
                    result = make_rpc_call(
                        network,
                        "eth_call",
                        [{
                            "to": address,
                            "data": voter_data
                        }, "latest"]
                    )
                    
                    if result and result != "0x" and len(result) > 66:
                        print(f"   ✅ getRegisteredVoters(0): Has data ({len(result)} chars)")
                        
                        # Try to decode first address from array
                        if len(result) > 130:  # Has at least one address
                            # Skip array length info and get first address
                            first_addr_data = result[130:194]  # 32 bytes for first address
                            if len(first_addr_data) == 64:
                                first_addr = "0x" + first_addr_data[24:]  # Last 20 bytes
                                print(f"   📋 First voter address: {first_addr}")
                        
                    else:
                        print(f"   ⚪ getRegisteredVoters(0): No data")
                        
                except Exception as e:
                    if "execution reverted" not in str(e):
                        print(f"   ❌ getRegisteredVoters error: {str(e)[:50]}")
                
                # Try getRegisteredVotersAndRegistrationWeights()
                try:
                    weights_data = "0x9d0881cd" + "0" * 56  # epoch 0
                    result = make_rpc_call(
                        network,
                        "eth_call",
                        [{
                            "to": address,
                            "data": weights_data
                        }, "latest"]
                    )
                    
                    if result and result != "0x" and len(result) > 66:
                        print(f"   ✅ getVotersAndWeights(0): Has data ({len(result)} chars)")
                        print(f"   📊 This could be our VoterRegistry!")
                        return address  # Found it!
                    else:
                        print(f"   ⚪ getVotersAndWeights(0): No data")
                        
                except Exception as e:
                    if "execution reverted" not in str(e):
                        print(f"   ❌ getVotersAndWeights error: {str(e)[:50]}")
            
            else:
                print(f"⚪ {address}: No contract")
                
        except Exception as e:
            print(f"❌ {address}: Error - {str(e)[:50]}")
    
    return None

if __name__ == "__main__":
    print("🔍 ALTERNATIVE FTSO DATA DISCOVERY")
    print("=" * 50)
    
    # Method 1: Look for events in recent blocks
    get_recent_blocks_with_events()
    
    # Method 2: Try known addresses
    voter_registry = try_known_ftso_addresses()
    
    if voter_registry:
        print(f"\\n🎯 FOUND VOTER REGISTRY: {voter_registry}")
    else:
        print(f"\\n❌ No VoterRegistry found in tested addresses")
