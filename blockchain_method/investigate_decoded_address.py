#!/usr/bin/env python3
"""
Investigate the decoded address from getAllProviders() result.
"""

from flare_rpc_new import make_rpc_call
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def investigate_decoded_address():
    """
    The large value 1,086,965,877,339,141,057,164,610,075,730,811,582,279,207,373,299
    converts to hex: 0xbe653c54df337f13fcb726101388f4a4803049f3
    
    This is exactly 40 chars - an Ethereum address!
    """
    
    decoded_address = "0xbe653c54df337f13fcb726101388f4a4803049f3"
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    
    print("🔍 INVESTIGATING DECODED ADDRESS")
    print("=" * 60)
    print(f"Decoded Address: {decoded_address}")
    print(f"Bifrost Address: {bifrost_address}")
    print()
    
    # Check if this address has any code
    try:
        code_result = make_rpc_call(
            "flare",
            "eth_getCode",
            [decoded_address, "latest"]
        )
        
        if code_result and code_result != "0x":
            print(f"✅ Address has contract code: {len(code_result)} chars")
        else:
            print("⚪ Address has no contract code (EOA)")
            
    except Exception as e:
        print(f"❌ Error checking code: {e}")
    
    # Check balance
    try:
        balance_result = make_rpc_call(
            "flare",
            "eth_getBalance",
            [decoded_address, "latest"]
        )
        
        if balance_result:
            balance = int(balance_result, 16)
            print(f"💰 Balance: {balance:,} wei ({balance / 1e18:.6f} FLR)")
            
    except Exception as e:
        print(f"❌ Error checking balance: {e}")

def test_address_relationships():
    """
    Test if this decoded address has any relationship with Bifrost.
    """
    
    decoded_address = "0xbe653c54df337f13fcb726101388f4a4803049f3"
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    wnat_contract = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"
    
    print("\\n🔍 TESTING ADDRESS RELATIONSHIPS")
    print("=" * 60)
    
    # Test if decoded address is delegating to Bifrost
    delegation_functions = {
        "delegateOf(address)": "0x9d1b464a",
        "votePowerOf(address)": "0x4ee2cd7e",
        "balanceOf(address)": "0x70a08231",
        "delegatedVotePower(address)": "0x6af1bdc0",
    }
    
    print(f"📋 Testing decoded address: {decoded_address}")
    
    for func_name, func_sig in delegation_functions.items():
        try:
            call_data = f"{func_sig}{decoded_address[2:].zfill(64)}"
            
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
                    print(f"  ✅ {func_name:<25}: {value:,}")
                    
                    if value == 1683080166:
                        print(f"      🎯 EXACT MATCH! This address has Bifrost's vote power!")
                elif len(result) == 66 and result.startswith("0x000000000000000000000000"):
                    # Might be an address
                    addr = "0x" + result[-40:]
                    print(f"  🏠 {func_name:<25}: {addr}")
                    
                    if addr.lower() == bifrost_address.lower():
                        print(f"      🎯 This address delegates to Bifrost!")
            else:
                print(f"  ⚪ {func_name:<25}: No data")
                
        except Exception as e:
            if "execution reverted" not in str(e):
                print(f"  ❌ {func_name:<25}: {str(e)[:30]}")

def test_vote_power_transfer():
    """
    Test if there's a vote power transfer from decoded address to Bifrost.
    """
    
    decoded_address = "0xbe653c54df337f13fcb726101388f4a4803049f3"
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    wnat_contract = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"
    
    print("\\n🔍 TESTING VOTE POWER TRANSFER")
    print("=" * 60)
    
    # Test vote power from decoded address to Bifrost
    try:
        # votePowerFromTo(from, to)
        func_sig = "0x2ff31d3e"
        call_data = f"{func_sig}{decoded_address[2:].zfill(64)}{bifrost_address[2:].zfill(64)}"
        
        result = make_rpc_call(
            "flare",
            "eth_call",
            [{
                "to": wnat_contract,
                "data": call_data
            }, "latest"]
        )
        
        if result and result != "0x":
            value = int(result, 16)
            print(f"✅ Vote power from decoded to Bifrost: {value:,}")
            
            if value == 1683080166:
                print(f"    🎯 EXACT MATCH! Found the delegation!")
        else:
            print("⚪ No vote power transfer found")
            
    except Exception as e:
        print(f"❌ Error testing vote power transfer: {e}")
    
    # Test the reverse
    try:
        call_data = f"{func_sig}{bifrost_address[2:].zfill(64)}{decoded_address[2:].zfill(64)}"
        
        result = make_rpc_call(
            "flare",
            "eth_call",
            [{
                "to": wnat_contract,
                "data": call_data
            }, "latest"]
        )
        
        if result and result != "0x":
            value = int(result, 16)
            print(f"✅ Vote power from Bifrost to decoded: {value:,}")
        else:
            print("⚪ No reverse vote power transfer found")
            
    except Exception as e:
        print(f"❌ Error testing reverse transfer: {e}")

def test_at_target_block():
    """
    Test vote power at the target block from the screenshot.
    """
    
    decoded_address = "0xbe653c54df337f13fcb726101388f4a4803049f3"
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    wnat_contract = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"
    target_block = 44798407  # From screenshot
    
    print("\\n🔍 TESTING AT TARGET BLOCK")
    print("=" * 60)
    print(f"Target Block: {target_block:,}")
    
    # Test functions with block parameter
    block_functions = {
        "votePowerOfAt(address,uint256)": "0x92bfe6a8",
        "balanceOfAt(address,uint256)": "0x4ee2cd7e",
    }
    
    addresses_to_test = [
        ("Decoded Address", decoded_address),
        ("Bifrost Address", bifrost_address),
    ]
    
    for addr_name, address in addresses_to_test:
        print(f"\\n📋 {addr_name}: {address}")
        
        for func_name, func_sig in block_functions.items():
            try:
                call_data = f"{func_sig}{address[2:].zfill(64)}{target_block:064x}"
                
                result = make_rpc_call(
                    "flare",
                    "eth_call",
                    [{
                        "to": wnat_contract,
                        "data": call_data
                    }, "latest"]
                )
                
                if result and result != "0x":
                    value = int(result, 16)
                    print(f"  ✅ {func_name:<25}: {value:,}")
                    
                    if value == 1683080166:
                        print(f"      🎯 EXACT MATCH! Found Bifrost vote power at target block!")
                    elif value > 1000000000:
                        print(f"      📊 Large value")
                else:
                    print(f"  ⚪ {func_name:<25}: No data")
                    
            except Exception as e:
                if "execution reverted" not in str(e):
                    print(f"  ❌ {func_name:<25}: {str(e)[:20]}")

def main():
    print("🎯 INVESTIGATING DECODED ADDRESS FROM getAllProviders()")
    print("📍 Large value decoded to: 0xbe653c54df337f13fcb726101388f4a4803049f3")
    print()
    
    investigate_decoded_address()
    test_address_relationships()
    test_vote_power_transfer()
    test_at_target_block()

if __name__ == "__main__":
    main()
