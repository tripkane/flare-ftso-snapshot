#!/usr/bin/env python3
"""
Debug FlareContractRegistry to understand its interface
"""

from flare_rpc_new import make_rpc_call

def test_registry_functions():
    """Test various function signatures on FlareContractRegistry"""
    registry_address = "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019"
    network = "flare"
    
    # First check if the contract exists
    try:
        code_result = make_rpc_call(network, "eth_getCode", [registry_address, "latest"])
        if not code_result or code_result == "0x":
            print(f"❌ Contract at {registry_address} doesn't exist!")
            return
        print(f"✅ Contract exists (code length: {len(code_result)})")
    except Exception as e:
        print(f"❌ Error checking contract existence: {e}")
        return
    
    # Test common registry functions
    functions_to_test = {
        # Common contract registry functions
        "getAllContracts()": "0x36b4ca19",
        "getContractAddresses()": "0x4d5bddff", 
        "getContractAddressByName(string)": "0xb5981e99",
        "getContractAddressByHash(bytes32)": "0x2db0e4f2",
        
        # Standard contract functions
        "name()": "0x06fdde03",
        "owner()": "0x8da5cb5b",
        "governance()": "0x5aa6e675",
        
        # Flare-specific functions (guessing)
        "getVoterRegistry()": "0x9e7a13ad",
        "getFlareSystemsManager()": "0x4d2e5caf",
    }
    
    print(f"\\n🔍 Testing functions on FlareContractRegistry...")
    
    for func_name, signature in functions_to_test.items():
        try:
            result = make_rpc_call(
                network,
                "eth_call", 
                [{
                    "to": registry_address,
                    "data": signature
                }, "latest"]
            )
            
            if result and result != "0x":
                print(f"✅ {func_name}: {result[:50]}{'...' if len(result) > 50 else ''}")
            else:
                print(f"⚪ {func_name}: empty response")
                
        except Exception as e:
            error_msg = str(e)
            if "execution reverted" in error_msg:
                print(f"❌ {func_name}: execution reverted")
            else:
                print(f"❌ {func_name}: {error_msg[:50]}")

def test_getContractAddressByName_with_known_names():
    """Test getContractAddressByName with various contract name variations"""
    registry_address = "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019"
    network = "flare"
    
    # Try various name formats
    contract_names = [
        "VoterRegistry",
        "FlareSystemsManager",
        "RewardManager", 
        "WNat",
        "PriceSubmitter",
        "FtsoManager",
        "FtsoRegistry", 
        "AddressUpdater",
        "Inflation",
    ]
    
    print(f"\\n🔍 Testing contract name lookups...")
    
    from flare_rpc_new import encode_string_param
    
    for name in contract_names:
        try:
            # getContractAddressByName(string) - signature: 0xb5981e99
            encoded_name = encode_string_param(name)
            data = f"0xb5981e99{encoded_name}"
            
            result = make_rpc_call(
                network,
                "eth_call",
                [{
                    "to": registry_address, 
                    "data": data
                }, "latest"]
            )
            
            if result and result != "0x" and len(result) >= 66:
                address = "0x" + result[-40:]
                if address != "0x0000000000000000000000000000000000000000":
                    print(f"✅ {name}: {address}")
                else:
                    print(f"⚪ {name}: zero address")
            else:
                print(f"⚪ {name}: no result")
                
        except Exception as e:
            error_msg = str(e)
            if "execution reverted" not in error_msg:
                print(f"❌ {name}: {error_msg[:50]}")

if __name__ == "__main__":
    test_registry_functions()
    test_getContractAddressByName_with_known_names()
