#!/usr/bin/env python3
"""
Systematic test of all potential FTSO-related contracts and functions.
Focus on finding the exact method that returns the vote power values from the screenshot.
"""

from flare_rpc_new import make_rpc_call, FlareRPCError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_known_ftso_contracts():
    """
    Test known FTSO-related contracts systematically.
    Based on Flare documentation and common patterns.
    """
    
    # Target: Bifrost should return 1,683,080,166
    bifrost_address = "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c"
    target_value = 1683080166
    
    # Known contract addresses and their purposes
    contracts_to_test = {
        # System contracts
        "VotePowerContract": "0x1000000000000000000000000000000000000002",
        "SystemContract3": "0x1000000000000000000000000000000000000003",
        "SystemContract4": "0x1000000000000000000000000000000000000004", 
        "SystemContract5": "0x1000000000000000000000000000000000000005",
        
        # Registry contracts
        "FlareContractRegistry": "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019",
        
        # Common WNat addresses
        "WNat_Common": "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d",
        "WNat_Alt1": "0x96B41289D90444B8adD57e6F265DB5aE8651DF29", 
        "WNat_Alt2": "0x02f0826ef6aD107Cfc861152B32B52fD11BaB9ED",
        
        # Potential FTSO contracts (educated guesses)
        "FtsoRegistry": "0x6D222fb4544E1aFD1AD82d3C9C3f6E97Ff666666",  # Guess
        "FtsoManager": "0x7777777777777777777777777777777777777777",    # Guess
    }
    
    # Functions to test on each contract
    functions_to_test = {
        # Standard ERC20/vote power functions
        "balanceOf(address)": "0x70a08231",
        "votePowerOf(address)": "0x142d1018", 
        "delegatedVotePowerOf(address)": "0x2ff31d3e",
        "totalVotePowerOf(address)": "0xf007d544",
        
        # FTSO-specific functions (from documentation)
        "getCurrentPrice(uint256)": "0x7dc0d1d0",
        "getVotePowerOf(address)": "0x8b7ab1dc",
        "getProviderVotePower(address)": "0x9e7a13ad",
        "getFtsoVotePower(address)": "0x4d2e5caf",
        
        # No-parameter functions that might return provider lists
        "getAllProviders()": "0x5aa6e675",
        "getActiveProviders()": "0x570ca735", 
        "getCurrentProviders()": "0x7dc0d1d0",
        "getRegisteredProviders()": "0x36b4ca19",
    }
    
    print("🔍 SYSTEMATIC FTSO CONTRACT TESTING")
    print("=" * 80)
    print(f"Target: Bifrost ({bifrost_address}) = {target_value:,}")
    print("=" * 80)
    
    matches_found = []
    
    for contract_name, contract_addr in contracts_to_test.items():
        print(f"\\n📋 Testing {contract_name}: {contract_addr}")
        print("-" * 60)
        
        # First check if contract exists
        try:
            code_result = make_rpc_call("flare", "eth_getCode", [contract_addr, "latest"])
            if not code_result or code_result == "0x":
                print("❌ Contract doesn't exist")
                continue
                
            print(f"✅ Contract exists ({len(code_result)} chars)")
            
        except Exception as e:
            print(f"❌ Error checking contract: {e}")
            continue
        
        # Test each function
        for func_name, func_sig in functions_to_test.items():
            try:
                # Prepare function call data
                if "address" in func_name.lower():
                    # Function takes address parameter
                    call_data = f"{func_sig}{bifrost_address[2:].zfill(64)}"
                else:
                    # Function takes no parameters
                    call_data = func_sig
                
                # Make the call
                result = make_rpc_call(
                    "flare",
                    "eth_call",
                    [{
                        "to": contract_addr,
                        "data": call_data
                    }, "latest"]
                )
                
                if result and result != "0x":
                    # Try to decode as single uint256
                    if len(result) == 66:  # 0x + 64 chars = single uint256
                        value = int(result, 16)
                        
                        print(f"  ✅ {func_name:<30}: {value:,}")
                        
                        # Check if this matches our target
                        if value == target_value:
                            print(f"      🎯 EXACT MATCH! Found target value!")
                            matches_found.append({
                                "contract": contract_name,
                                "address": contract_addr,
                                "function": func_name,
                                "signature": func_sig,
                                "value": value
                            })
                        elif value > 1000000000:  # Close to target range
                            print(f"      📊 Large value - potential match")
                            
                    else:
                        # Complex return data
                        print(f"  📄 {func_name:<30}: Complex data ({len(result)} chars)")
                        
                else:
                    print(f"  ⚪ {func_name:<30}: No data")
                    
            except Exception as e:
                error_msg = str(e)
                if "execution reverted" in error_msg:
                    print(f"  ❌ {func_name:<30}: Reverted")
                else:
                    print(f"  ❌ {func_name:<30}: {error_msg[:30]}")
    
    print("\\n" + "=" * 80)
    print("🎯 RESULTS SUMMARY")
    print("=" * 80)
    
    if matches_found:
        print("🎉 EXACT MATCHES FOUND:")
        for match in matches_found:
            print(f"  Contract: {match['contract']} ({match['address']})")
            print(f"  Function: {match['function']} ({match['signature']})")
            print(f"  Value: {match['value']:,}")
            print()
    else:
        print("❌ No exact matches found.")
        print("\\n💡 Next steps:")
        print("- Try different function signatures")
        print("- Look for provider registry contracts")
        print("- Check if values need scaling/conversion")
        print("- Examine contract source code for correct function names")

def test_provider_lists():
    """
    Test functions that might return lists of providers with their vote powers.
    """
    print("\\n🔍 TESTING PROVIDER LIST FUNCTIONS")
    print("=" * 60)
    
    contracts = [
        ("VotePowerContract", "0x1000000000000000000000000000000000000002"),
        ("FlareRegistry", "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019"),
    ]
    
    # Functions that might return arrays/lists
    list_functions = {
        "getAllContracts()": "0x36b4ca19",
        "getAllProviders()": "0x5aa6e675", 
        "getProviders()": "0x570ca735",
        "getDataProviders()": "0x7dc0d1d0",
        "getRegisteredProviders()": "0x9e7a13ad",
    }
    
    for contract_name, contract_addr in contracts:
        print(f"\\n📋 {contract_name}: {contract_addr}")
        
        for func_name, func_sig in list_functions.items():
            try:
                result = make_rpc_call(
                    "flare",
                    "eth_call", 
                    [{
                        "to": contract_addr,
                        "data": func_sig
                    }, "latest"]
                )
                
                if result and result != "0x":
                    print(f"  ✅ {func_name:<25}: Got data ({len(result)} chars)")
                    if len(result) > 200:  # Likely array data
                        print(f"      📄 Large response - likely contains provider list")
                else:
                    print(f"  ⚪ {func_name:<25}: No data")
                    
            except Exception as e:
                if "execution reverted" not in str(e):
                    print(f"  ❌ {func_name:<25}: {str(e)[:30]}")

def main():
    test_known_ftso_contracts()
    test_provider_lists()

if __name__ == "__main__":
    main()
