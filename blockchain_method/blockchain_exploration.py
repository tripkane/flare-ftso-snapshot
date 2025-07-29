#!/usr/bin/env python3
"""
Systematic exploration of Flare FTSO contracts to find the right data.
"""

from flare_rpc_new import make_rpc_call
from typing import Dict, List, Any

def try_ftso_specific_functions(address: str, network: str = "flare") -> Dict[str, str]:
    """
    Try FTSO-specific function signatures
    """
    # These are educated guesses based on FTSO system
    functions = {
        'getCurrentPrices()': '0x7dc0d1d0',
        'getDataProviders()': '0x570ca735',
        'getAllDataProviders()': '0x5aa6e675', 
        'getVotePowers()': '0x8b7ab1dc',
        'getCurrentVotePower()': '0x2d2c5565',
        'getActiveDataProviders()': '0x9e7a13ad',
        'getFtsoRegistry()': '0x8c9d28b7',
        'getFtsoManager()': '0x4d2e5caf',
        'name()': '0x06fdde03',
        'symbol()': '0x95d89b41',
        'totalSupply()': '0x18160ddd',
    }
    
    results = {}
    
    for func_name, sig in functions.items():
        try:
            result = make_rpc_call('eth_call', [{
                'to': address,
                'data': sig
            }, 'latest'], network)
            
            response = result.get('result', '0x')
            if response and response != '0x' and len(response) > 2:
                results[func_name] = response
                
        except Exception as e:
            if "execution reverted" not in str(e):
                results[func_name] = f"Error: {str(e)[:50]}"
            
    return results

def decode_address_from_response(response: str) -> str:
    """Decode an address from a 32-byte response"""
    if len(response) == 66:  # 0x + 64 chars
        return "0x" + response[-40:]
    return response

def main():
    print("🔍 SYSTEMATIC FLARE BLOCKCHAIN EXPLORATION")
    print("=" * 60)
    
    # Known contract addresses to explore
    contracts_to_check = {
        "VotePowerContract": "0x1000000000000000000000000000000000000002",
        "SystemContract3": "0x1000000000000000000000000000000000000003", 
        "SystemContract4": "0x1000000000000000000000000000000000000004",
        "SystemContract5": "0x1000000000000000000000000000000000000005",
        "SongbirdRegistry": "0xbfA12e4E1411B62EdA8B035d71735667422A6A9e",  # From your link
        "FlareRegistry": "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019",  # Common FTSO Registry
    }
    
    for contract_name, address in contracts_to_check.items():
        print(f"\\n{'='*20} {contract_name} {'='*20}")
        print(f"Address: {address}")
        
        # Check if it exists on Flare
        try:
            code_result = make_rpc_call('eth_getCode', [address, 'latest'], "flare")
            code = code_result.get('result', '0x')
            
            if not code or code == '0x':
                print("❌ Contract doesn't exist on Flare")
                continue
                
            print(f"✅ Contract exists (code: {len(code)} chars)")
            
            # Try FTSO functions  
            print("\\n--- Function Testing ---")
            ftso_results = try_ftso_specific_functions(address, "flare")
            
            for func, result in ftso_results.items():
                if result.startswith("0x"):
                    # Try to decode if it looks like an address
                    if len(result) == 66:
                        decoded_addr = decode_address_from_response(result)
                        print(f"  ✅ {func}: {decoded_addr}")
                    else:
                        print(f"  ✅ {func}: {result[:50]}...")
                else:
                    print(f"  ❌ {func}: {result}")
                    
        except Exception as e:
            print(f"❌ Error checking {contract_name}: {e}")
    
    print(f"\\n{'='*60}")
    print("🎯 ANALYSIS:")
    print("- Look for functions returning arrays or multiple addresses")
    print("- Find contracts that manage provider lists") 
    print("- Check returned addresses for provider-specific data")

if __name__ == "__main__":
    main()
