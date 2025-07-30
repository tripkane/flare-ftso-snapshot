#!/usr/bin/env python3
"""
FTSO Contract interfaces for getting proper vote power data.
"""

from flare_rpc_new import make_rpc_call, FlareRPCError
from typing import Dict, List, Any, Optional

# Known FTSO contract addresses
FTSO_CONTRACTS = {
    "flare": {
        "FtsoRegistry": "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019",  # Main FTSO Registry
        "VotePowerManager": "0x1000000000000000000000000000000000000002",  # Vote Power Contract
        "FtsoManager": "0x1000000000000000000000000000000000000003",  # FTSO Manager
    },
    "songbird": {
        "FtsoRegistry": "0xbfA12e4E1411B62EdA8B035d71735667422A6A9e",  # From your link
        "VotePowerManager": "0x1000000000000000000000000000000000000002",
        "FtsoManager": "0x1000000000000000000000000000000000000003",
    }
}

# Common FTSO function signatures
FTSO_FUNCTIONS = {
    "getAllCurrentPrices": "0x8b9e4f93",
    "getDataProviders": "0x570ca735", 
    "getAllDataProviders": "0x5aa6e675",
    "getCurrentVotePower": "0x2d2c5565",
    "getVotePowerOf": "0xb5ab58dc",  # getVotePowerOf(address)
    "totalSupply": "0x18160ddd",
    "name": "0x06fdde03",
    "symbol": "0x95d89b41",
}

def call_ftso_function(contract_address: str, function_sig: str, params: List[str] = None, network: str = "flare") -> Optional[str]:
    """
    Call a function on an FTSO contract using eth_call
    """
    try:
        # Construct the call data
        call_data = function_sig
        if params:
            for param in params:
                # Pad each parameter to 32 bytes (64 hex chars)
                padded_param = param.zfill(64)
                call_data += padded_param
        
        # Make the RPC call
        result = make_rpc_call('eth_call', [{
            'to': contract_address,
            'data': call_data
        }, 'latest'], network)
        
        return result.get('result', '0x')
        
    except Exception as e:
        print(f"Error calling function {function_sig} on {contract_address}: {e}")
        return None

def get_ftso_providers_from_contract(network: str = "flare") -> List[Dict[str, Any]]:
    """
    Get FTSO provider data directly from the FTSO Registry contract
    """
    try:
        ftso_registry = FTSO_CONTRACTS[network]["FtsoRegistry"]
        
        print(f"Querying FTSO Registry: {ftso_registry} on {network}")
        
        # First, check if the contract exists
        code = call_ftso_function(ftso_registry, "0x", [], network)
        if not code or code == "0x":
            print(f"FTSO Registry contract not found at {ftso_registry}")
            return []
        
        print(f"✓ Contract exists (code length: {len(code)} chars)")
        
        # Try to get all data providers
        providers_data = call_ftso_function(ftso_registry, FTSO_FUNCTIONS["getAllDataProviders"], [], network)
        
        if providers_data and providers_data != "0x":
            print(f"✓ Got providers data: {providers_data[:50]}...")
            # TODO: Parse the returned data according to the contract ABI
            return parse_providers_data(providers_data)
        else:
            print("✗ No providers data returned")
            
        # Try alternative functions
        for func_name, func_sig in FTSO_FUNCTIONS.items():
            if func_name in ["name", "symbol", "totalSupply"]:
                result = call_ftso_function(ftso_registry, func_sig, [], network)
                if result and result != "0x":
                    print(f"✓ {func_name}: {result}")
                else:
                    print(f"✗ {func_name}: no response")
        
        return []
        
    except Exception as e:
        raise FlareRPCError(f"Failed to get FTSO providers from contract: {e}")

def parse_providers_data(raw_data: str) -> List[Dict[str, Any]]:
    """
    Parse the raw hex data returned from FTSO contract calls
    This decodes the array of addresses returned by getAllDataProviders
    """
    try:
        if not raw_data or raw_data == "0x":
            return []
            
        # Remove 0x prefix
        data = raw_data[2:]
        
        # First 32 bytes (64 chars) is the offset to the array
        # Second 32 bytes is the length of the array
        if len(data) < 128:
            return []
            
        # Get array length from bytes 64-128
        array_length_hex = data[64:128]
        array_length = int(array_length_hex, 16)
        
        print(f"Found {array_length} data providers in contract response")
        
        providers = []
        
        # Each address is 32 bytes (64 hex chars), but addresses are 20 bytes
        # They're padded with zeros at the beginning
        for i in range(array_length):
            start_pos = 128 + (i * 64)
            end_pos = start_pos + 64
            
            if end_pos <= len(data):
                # Extract the 40-character address (last 40 chars of the 64-char field)
                address_hex = data[start_pos + 24:end_pos]  # Skip 24 chars of padding
                address = "0x" + address_hex
                
                providers.append({
                    "address": address,
                    "index": i
                })
                
        return providers
        
    except Exception as e:
        print(f"Error parsing providers data: {e}")
        return []

def test_ftso_contracts(network: str = "flare") -> None:
    """
    Test FTSO contract connectivity and functions
    """
    print(f"=== Testing FTSO Contracts on {network} ===")
    
    contracts = FTSO_CONTRACTS[network]
    
    for contract_name, address in contracts.items():
        print(f"\nTesting {contract_name}: {address}")
        
        # Check if contract exists
        try:
            result = make_rpc_call('eth_getCode', [address, 'latest'], network)
            code = result.get('result', '0x')
            
            if code and code != '0x' and len(code) > 2:
                print(f"  ✓ Contract exists (code: {len(code)} chars)")
                
                # Test basic functions
                for func_name, func_sig in list(FTSO_FUNCTIONS.items())[:3]:
                    try:
                        response = call_ftso_function(address, func_sig, [], network)
                        if response and response != '0x':
                            print(f"  ✓ {func_name}: {response[:30]}...")
                        else:
                            print(f"  ✗ {func_name}: no response")
                    except Exception as e:
                        print(f"  ✗ {func_name}: {str(e)[:50]}")
                        
            else:
                print(f"  ✗ No contract code found")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")

if __name__ == "__main__":
    # Test the FTSO contracts
    test_ftso_contracts("flare")
    test_ftso_contracts("songbird")
