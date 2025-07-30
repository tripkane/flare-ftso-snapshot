#!/usr/bin/env python3
"""
Find real Flare contract addresses using FlareContractRegistry
"""

from flare_rpc_new import make_rpc_call, encode_string_param

def find_contract_address(contract_name: str, network: str = "flare") -> str:
    """
    Find contract address using FlareContractRegistry.
    """
    registry_address = "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019"
    
    # getContractAddressByName(string) - signature: 0xb5981e99
    get_contract_data = f"0xb5981e99{encode_string_param(contract_name)}"
    
    try:
        result = make_rpc_call(
            network,
            "eth_call",
            [{
                "to": registry_address,
                "data": get_contract_data
            }, "latest"]
        )
        
        if result and result != "0x" and len(result) >= 66:
            # Decode address from result (take last 40 chars)
            address = "0x" + result[-40:]
            return address
        else:
            return None
            
    except Exception as e:
        print(f"Error finding {contract_name}: {e}")
        return None

def main():
    print("🔍 Finding Real Flare Contract Addresses")
    print("=" * 50)
    
    contracts = [
        "VoterRegistry",
        "FlareSystemsManager", 
        "FlareSystemsCalculator",
        "ProtocolsV2",
        "RewardManager",
        "WNat",
        "EntityManager",
        "Relay",
        "Submission"
    ]
    
    found_contracts = {}
    
    for contract_name in contracts:
        print(f"\\nLooking up {contract_name}...")
        address = find_contract_address(contract_name, "flare")
        
        if address and address != "0x0000000000000000000000000000000000000000":
            print(f"✅ {contract_name}: {address}")
            found_contracts[contract_name] = address
        else:
            print(f"❌ {contract_name}: Not found or zero address")
    
    print("\\n" + "=" * 50)
    print("📋 Found Contracts:")
    print("=" * 50)
    
    for name, addr in found_contracts.items():
        print(f"{name}: {addr}")
    
    return found_contracts

if __name__ == "__main__":
    main()
