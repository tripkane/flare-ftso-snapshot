#!/usr/bin/env python3
"""
Decode the large value returned by getAllProviders() and explore delegation patterns.
Focus on finding Bifrost vote power: 1,683,080,166 from Reward Epoch 313.
"""

from flare_rpc_new import make_rpc_call
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def decode_large_value():
    """
    Decode the large value: 1,086,965,877,339,141,057,164,610,075,730,811,582,279,207,373,299
    This might contain encoded address and vote power data.
    """
    
    large_value = 1086965877339141057164610075730811582279207373299
    
    print("🔍 DECODING LARGE VALUE FROM getAllProviders()")
    print("=" * 60)
    print(f"Value: {large_value:,}")
    print(f"Hex: 0x{large_value:x}")
    
    hex_str = f"{large_value:x}"
    print(f"Hex length: {len(hex_str)} chars")
    
    # Try to interpret as packed data
    if len(hex_str) >= 40:  # At least one address worth
        print("\\nPossible address interpretations:")
        
        # Try extracting 20-byte addresses from different positions
        for i in range(0, min(len(hex_str) - 40, 100), 8):
            addr_hex = hex_str[i:i+40]
            if len(addr_hex) == 40:
                address = "0x" + addr_hex
                print(f"  Position {i:2d}: {address}")
                
                # Check if this looks like a known provider
                if address.lower() == "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c":
                    print(f"      🎯 BIFROST FOUND!")
    
    # Try interpreting as multiple uint256 values
    print("\\nTrying to split into 32-byte chunks:")
    hex_padded = hex_str.zfill(64)  # Pad to multiple of 64
    
    for i in range(0, len(hex_padded), 64):
        chunk = hex_padded[i:i+64]
        if len(chunk) == 64:
            value = int(chunk, 16)
            print(f"  Chunk {i//64}: {value:,}")
            
            # Check if this could be Bifrost's vote power
            if value == 1683080166:
                print(f"      🎯 BIFROST VOTE POWER FOUND!")

def test_delegation_functions():
    """
    Test delegation-related functions to find where vote power comes from.
    Since Bifrost shows 0 direct balance, vote power likely comes from delegation.
    """
    
    print("\\n🔍 TESTING DELEGATION FUNCTIONS")
    print("=" * 60)
    
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    wnat_contract = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"
    
    # Delegation-related function signatures
    delegation_functions = {
        # Who is Bifrost delegating to?
        "delegatesOf(address)": "0x8c8ff3a8",
        "delegateOf(address)": "0x9d1b464a", 
        "getDelegates(address)": "0x91c1ad6e",
        
        # Who is delegating to Bifrost?
        "delegatorsOf(address)": "0x426748c2",
        "getDelegators(address)": "0x5b7e73a6",
        
        # Vote power delegation amounts
        "votePowerFromTo(address,address)": "0x2ff31d3e",
        "delegatedVotePower(address)": "0x6af1bdc0",
        "receivedDelegation(address)": "0x4b6753bc",
        
        # Total delegated vote power
        "totalDelegatedVotePower(address)": "0x8b7ab1dc",
        "totalReceivedDelegation(address)": "0x9e7a13ad",
    }
    
    print(f"Testing on WNat contract: {wnat_contract}")
    print(f"Target address (Bifrost): {bifrost_address}")
    print("-" * 60)
    
    for func_name, func_sig in delegation_functions.items():
        try:
            # Prepare call data
            call_data = f"{func_sig}{bifrost_address[2:].zfill(64)}"
            
            result = make_rpc_call(
                "flare",
                "eth_call",
                [{
                    "to": wnat_contract,
                    "data": call_data
                }, "latest"]
            )
            
            if result and result != "0x":
                if len(result) == 66:  # Single uint256
                    value = int(result, 16)
                    print(f"✅ {func_name:<30}: {value:,}")
                    
                    # Check if this matches our target
                    if value == 1683080166:
                        print(f"      🎯 EXACT MATCH! Found Bifrost vote power!")
                    elif value > 1000000000:
                        print(f"      📊 Large value - potential match")
                        
                else:
                    print(f"📄 {func_name:<30}: Complex data ({len(result)} chars)")
                    
                    # Try to decode if it looks like address array
                    if len(result) > 130:  # Might be array
                        print(f"      Might contain addresses or array data")
            else:
                print(f"⚪ {func_name:<30}: No data")
                
        except Exception as e:
            if "execution reverted" not in str(e):
                print(f"❌ {func_name:<30}: {str(e)[:30]}")

def test_vote_power_at_block():
    """
    Test vote power functions with specific block numbers.
    The screenshot shows Vote Power Block: 44,798,407
    """
    
    print("\\n🔍 TESTING VOTE POWER AT SPECIFIC BLOCK")
    print("=" * 60)
    
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    target_block = 44798407  # From screenshot
    current_block = 44944340  # From our earlier test
    
    contracts_to_test = [
        ("VotePowerContract", "0x1000000000000000000000000000000000000002"),
        ("WNat", "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"),
    ]
    
    # Functions that take block parameter
    block_functions = {
        "votePowerOfAt(address,uint256)": "0x92bfe6a8",
        "balanceOfAt(address,uint256)": "0x4ee2cd7e",
        "totalSupplyAt(uint256)": "0x981b24d0",
        "delegatedVotePowerOfAt(address,uint256)": "0x6af1bdc0",
    }
    
    blocks_to_test = [target_block, current_block, current_block - 1000]
    
    for contract_name, contract_addr in contracts_to_test:
        print(f"\\n📋 {contract_name}: {contract_addr}")
        
        for block_num in blocks_to_test:
            print(f"  Block: {block_num:,}")
            
            for func_name, func_sig in block_functions.items():
                try:
                    # Prepare call data: function(address, uint256)
                    call_data = f"{func_sig}{bifrost_address[2:].zfill(64)}{block_num:064x}"
                    
                    result = make_rpc_call(
                        "flare",
                        "eth_call",
                        [{
                            "to": contract_addr,
                            "data": call_data
                        }, "latest"]
                    )
                    
                    if result and result != "0x":
                        value = int(result, 16)
                        print(f"    ✅ {func_name:<25}: {value:,}")
                        
                        if value == 1683080166:
                            print(f"        🎯 EXACT MATCH! Found Bifrost vote power!")
                        elif value > 1000000000:
                            print(f"        📊 Large value")
                    else:
                        print(f"    ⚪ {func_name:<25}: No data")
                        
                except Exception as e:
                    if "execution reverted" not in str(e):
                        print(f"    ❌ {func_name:<25}: {str(e)[:20]}")

def test_ftso_specific_functions():
    """
    Test FTSO-specific functions that might return provider vote powers.
    """
    
    print("\\n🔍 TESTING FTSO-SPECIFIC FUNCTIONS")
    print("=" * 60)
    
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    epoch_313 = 313
    
    # FTSO-related contracts
    ftso_contracts = {
        "VotePowerContract": "0x1000000000000000000000000000000000000002",
        "FtsoManager": "0x1000000000000000000000000000000000000003",
        "FtsoRewardManager": "0x1000000000000000000000000000000000000004",
        "FtsoRegistry": "0x1000000000000000000000000000000000000006",
    }
    
    # FTSO-specific functions
    ftso_functions = {
        # Provider vote power queries
        "getVotePowerOfAt(address,uint256)": "0x92bfe6a8",
        "getProviderVotePowerAt(address,uint256)": "0x8b7ab1dc", 
        "getEpochVotePowerOf(uint256,address)": "0x9e7a13ad",
        
        # Epoch-specific queries
        "getCurrentEpochData()": "0x2ec0b0d4",
        "getEpochData(uint256)": "0x4ee2cd7e",
        "getProviderDataForEpoch(uint256,address)": "0x6af1bdc0",
        
        # Provider status
        "getProviderVotePower(address)": "0x4b6753bc",
        "isProviderActive(address)": "0x426748c2",
        "getProviderWeights(uint256)": "0x5b7e73a6",
    }
    
    for contract_name, contract_addr in ftso_contracts.items():
        print(f"\\n📋 {contract_name}: {contract_addr}")
        
        for func_name, func_sig in ftso_functions.items():
            try:
                # Different call data based on function signature
                if "uint256,address" in func_name:
                    # Epoch first, then address
                    call_data = f"{func_sig}{epoch_313:064x}{bifrost_address[2:].zfill(64)}"
                elif "address,uint256" in func_name:
                    # Address first, then epoch/block
                    call_data = f"{func_sig}{bifrost_address[2:].zfill(64)}{epoch_313:064x}"
                elif "address" in func_name:
                    # Just address
                    call_data = f"{func_sig}{bifrost_address[2:].zfill(64)}"
                elif "uint256" in func_name:
                    # Just epoch
                    call_data = f"{func_sig}{epoch_313:064x}"
                else:
                    # No parameters
                    call_data = func_sig
                
                result = make_rpc_call(
                    "flare",
                    "eth_call",
                    [{
                        "to": contract_addr,
                        "data": call_data
                    }, "latest"]
                )
                
                if result and result != "0x":
                    if len(result) == 66:  # Single uint256
                        value = int(result, 16)
                        print(f"  ✅ {func_name:<35}: {value:,}")
                        
                        if value == 1683080166:
                            print(f"      🎯 EXACT MATCH! Found Bifrost vote power!")
                        elif value > 1000000000:
                            print(f"      📊 Large value")
                    else:
                        print(f"  📄 {func_name:<35}: Complex data ({len(result)} chars)")
                else:
                    print(f"  ⚪ {func_name:<35}: No data")
                    
            except Exception as e:
                if "execution reverted" not in str(e):
                    print(f"  ❌ {func_name:<35}: {str(e)[:20]}")

def main():
    print("🎯 TARGET: Find Bifrost vote power = 1,683,080,166 from Reward Epoch 313")
    print("📍 Vote Power Block: 44,798,407")
    print("🏪 Bifrost Address: 0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c")
    print()
    
    decode_large_value()
    test_delegation_functions() 
    test_vote_power_at_block()
    test_ftso_specific_functions()

if __name__ == "__main__":
    main()
