#!/usr/bin/env python3
"""
Try to find the actual WNat balances and delegations that determine vote power.
The vote power might come from WNat delegations rather than the VotePowerContract events.
"""

from flare_rpc_new import make_rpc_call, FlareRPCError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def try_wnat_contract_calls(network: str = "flare"):
    """
    Try to find WNat contract and get delegation balances.
    Vote power likely comes from WNat delegations.
    """
    
    # Common WNat contract addresses (need to find the real one)
    potential_wnat_addresses = [
        "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",  # Common WNat address
        "0x96B41289D90444B8adD57e6F265DB5aE8651DF29",  # Another possibility
        "0x02f0826ef6aD107Cfc861152B32B52fD11BaB9ED",  # Flare WNat
    ]
    
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    
    print("🔍 CHECKING WNAT CONTRACTS")
    print("=" * 50)
    
    for wnat_addr in potential_wnat_addresses:
        print(f"\\nTrying WNat at: {wnat_addr}")
        
        try:
            # Check if contract exists
            code_result = make_rpc_call(network, "eth_getCode", [wnat_addr, "latest"])
            if not code_result or code_result == "0x":
                print("❌ Contract doesn't exist")
                continue
            
            print(f"✅ Contract exists (code: {len(code_result)} chars)")
            
            # Try balanceOf(address) - 0x70a08231
            balance_data = f"0x70a08231{bifrost_address[2:].zfill(64)}"
            balance_result = make_rpc_call(network, "eth_call", [{"to": wnat_addr, "data": balance_data}, "latest"])
            
            if balance_result and balance_result != "0x":
                balance = int(balance_result, 16)
                print(f"✅ Bifrost balance: {balance:,}")
                
                # Check if this is close to our target
                if balance > 1000000000:  # Over 1B
                    print(f"🎯 This looks promising! Target: 1,683,080,166")
                    return balance
            else:
                print("❌ No balance found")
                
            # Try votePowerOf(address) - 0x142d1018
            vote_power_data = f"0x142d1018{bifrost_address[2:].zfill(64)}"
            vote_result = make_rpc_call(network, "eth_call", [{"to": wnat_addr, "data": vote_power_data}, "latest"])
            
            if vote_result and vote_result != "0x":
                vote_power = int(vote_result, 16)
                print(f"✅ Bifrost vote power: {vote_power:,}")
                
                if vote_power > 1000000000:
                    print(f"🎯 Vote power looks good! Target: 1,683,080,166")
                    return vote_power
            else:
                print("❌ No vote power found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return None

def explore_contract_functions(address: str, network: str = "flare"):
    """
    Try common function signatures on a contract to see what it supports.
    """
    
    common_functions = {
        # ERC20 functions
        "balanceOf(address)": "0x70a08231",
        "totalSupply()": "0x18160ddd",
        "name()": "0x06fdde03",
        "symbol()": "0x95d89b41",
        
        # Vote power functions
        "votePowerOf(address)": "0x142d1018",
        "votePowerOfAt(address,uint256)": "0x92bfe6a8",
        "totalVotePower()": "0xf007d544",
        "totalVotePowerAt(uint256)": "0x92ba6c16",
        
        # Delegation functions
        "delegateVotePower(address)": "0x7c3c0d0a",
        "delegatesOf(address)": "0x91c1ad6e",
        "votePowerFromTo(address,address)": "0x2ff31d3e",
    }
    
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    
    print(f"\\n🔍 Exploring functions on {address}")
    print("-" * 50)
    
    for func_name, signature in common_functions.items():
        try:
            if "address" in func_name:
                # Functions that take an address parameter
                data = f"{signature}{bifrost_address[2:].zfill(64)}"
            else:
                # Functions with no parameters
                data = signature
            
            result = make_rpc_call(network, "eth_call", [{"to": address, "data": data}, "latest"])
            
            if result and result != "0x":
                if len(result) <= 66:  # Single value
                    value = int(result, 16)
                    if value > 0:
                        print(f"✅ {func_name:<25}: {value:,}")
                        if value > 1000000000:  # Potential match
                            print(f"   🎯 Potential match! Target: 1,683,080,166")
                else:
                    print(f"✅ {func_name:<25}: Complex data ({len(result)} chars)")
            else:
                print(f"⚪ {func_name:<25}: No data")
                
        except Exception as e:
            if "execution reverted" not in str(e):
                print(f"❌ {func_name:<25}: {str(e)[:30]}")

def main():
    print("🔍 SEARCHING FOR ACTUAL VOTE POWER SOURCE")
    print("=" * 60)
    print("Target: Bifrost = 1,683,080,166")
    print("=" * 60)
    
    # Try WNat contracts first
    result = try_wnat_contract_calls("flare")
    
    if result:
        print(f"\\n🎯 FOUND POTENTIAL MATCH: {result:,}")
        return
    
    # If no luck with WNat, explore the VotePowerContract more thoroughly
    print("\\n🔍 EXPLORING VOTE POWER CONTRACT FUNCTIONS")
    vote_power_contract = "0x1000000000000000000000000000000000000002"
    explore_contract_functions(vote_power_contract, "flare")

if __name__ == "__main__":
    main()
