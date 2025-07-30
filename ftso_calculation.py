#!/usr/bin/env python3
"""
Proper FTSO vote power calculation following the official formula.

Based on:
- STP.01: 2.5% vote power cap
- FIP.03: Primary and secondary reward bands
- Flare FTSO documentation
"""

import json
from typing import Dict, List, Any, Optional
from flare_rpc_new import make_rpc_call, get_provider_name, FlareRPCError


def get_total_vote_power(block_number: int, network: str = "flare") -> int:
    """
    Get the total vote power (total WFLR supply) at a specific block.
    This is the denominator for percentage calculations.
    """
    try:
        # WFLR contract address (wrapped FLR)
        if network == "flare":
            wflr_contract = "0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d"  # WFLR on Flare
        else:
            wflr_contract = "0x02f0826ef6aD107Cfc861152B32B52fD11BaB9ED"  # WSGB on Songbird
        
        # Get total supply at the specific block
        result = make_rpc_call("eth_call", [{
            "to": wflr_contract,
            "data": "0x18160ddd"  # totalSupply() function signature
        }, hex(block_number)], network)
        
        total_supply = int(result["result"], 16)
        return total_supply
        
    except Exception as e:
        raise FlareRPCError(f"Failed to get total vote power: {e}")


def get_provider_vote_power(provider_address: str, block_number: int, network: str = "flare") -> int:
    """
    Get a provider's vote power (including delegations) at a specific block.
    """
    try:
        vote_contract = "0x1000000000000000000000000000000000000002"
        
        # Function signature for votePowerOfAt(address,uint256)
        # keccak256("votePowerOfAt(address,uint256)") = 0x7810b007...
        function_sig = "0x7810b007"
        address_param = provider_address[2:].zfill(64)  # Remove 0x and pad to 64 chars
        block_param = format(block_number, '064x')  # Block number as 64-char hex
        
        call_data = function_sig + address_param + block_param
        
        result = make_rpc_call("eth_call", [{
            "to": vote_contract,
            "data": call_data
        }, hex(block_number)], network)
        
        vote_power = int(result["result"], 16)
        return vote_power
        
    except Exception as e:
        print(f"Warning: Could not get vote power for {provider_address}: {e}")
        return 0


def apply_vote_power_cap(vote_power: int, total_vote_power: int, cap_percentage: float = 2.5) -> int:
    """
    Apply the FTSO vote power cap (2.5% of total vote power).
    
    Args:
        vote_power: Provider's raw vote power
        total_vote_power: Total vote power in the network
        cap_percentage: Cap percentage (default 2.5%)
    
    Returns:
        Capped vote power
    """
    cap_amount = int(total_vote_power * cap_percentage / 100)
    return min(vote_power, cap_amount)


def calculate_ftso_vote_power_percentages(network: str = "flare", vote_power_block: int = None) -> List[Dict[str, Any]]:
    """
    Calculate proper FTSO vote power percentages using the official formula.
    
    Args:
        network: "flare" or "songbird"
        vote_power_block: Specific block to query (from current reward epoch)
    
    Returns:
        List of providers with correct vote power percentages
    """
    try:
        # Use the vote power block from the screenshot if not provided
        if vote_power_block is None:
            if network == "flare":
                vote_power_block = 44798407  # From Flare FTSO Statistics screenshot
            else:
                # For Songbird, we'd need to look up the current epoch's vote power block
                from flare_rpc_new import get_latest_block
                vote_power_block = get_latest_block(network) - 5000
        
        print(f"Calculating FTSO vote power for {network} at block {vote_power_block}")
        
        # Get total vote power (total WFLR supply at the vote power block)
        total_vote_power = get_total_vote_power(vote_power_block, network)
        print(f"Total vote power at block {vote_power_block}: {total_vote_power:,}")
        
        # Known provider addresses from the screenshot and our mapping
        known_providers = [
            "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c",  # Bifrost Wallet
            "0x7b61f9f27153a4f2f57dc30bf08a8eb0ccb96c22",  # Flare.Space
            "0xbce1972de5d1598a948a36186ecebfd4690f3a5c",  # AlphaOracle
            "0x89e50dc0380e597ece79c8494baafd84537ad0d4",  # Atlas TSO
            "0x9c7a4c83842b29bb4a082b0e689cb9474bd938d0",  # Flare Oracle
            "0xdbf71d7840934eb82fa10173103d4e9fd4054dd1",  # NORTSO
            "0x9c7a4c83842b29bb4a082b0e689cb9474bd938d0",  # Other providers...
        ]
        
        providers = []
        total_capped_vote_power = 0
        
        # Calculate vote power for each known provider
        for address in known_providers:
            raw_vote_power = get_provider_vote_power(address, vote_power_block, network)
            
            if raw_vote_power > 0:
                # Apply 2.5% cap
                capped_vote_power = apply_vote_power_cap(raw_vote_power, total_vote_power, 2.5)
                total_capped_vote_power += capped_vote_power
                
                provider_data = {
                    "address": address,
                    "name": get_provider_name(address),
                    "raw_vote_power": raw_vote_power,
                    "capped_vote_power": capped_vote_power,
                    "vote_power_block": vote_power_block
                }
                providers.append(provider_data)
                
                print(f"  {provider_data['name']}: {raw_vote_power:,} -> {capped_vote_power:,} (capped)")
        
        # Calculate final percentages based on capped vote powers
        for provider in providers:
            if total_capped_vote_power > 0:
                percentage = (provider["capped_vote_power"] / total_capped_vote_power) * 100
                provider["vote_power_pct"] = round(percentage, 2)
            else:
                provider["vote_power_pct"] = 0.0
        
        # Sort by percentage descending
        providers.sort(key=lambda x: x["vote_power_pct"], reverse=True)
        
        print(f"\nTotal capped vote power: {total_capped_vote_power:,}")
        print(f"Vote power cap (2.5% of total): {int(total_vote_power * 0.025):,}")
        
        return providers
        
    except Exception as e:
        raise FlareRPCError(f"Failed to calculate FTSO vote power percentages: {e}")


def main():
    """Test the proper FTSO calculation"""
    print("=== Proper FTSO Vote Power Calculation ===")
    
    try:
        providers = calculate_ftso_vote_power_percentages("flare")
        
        print(f"\n=== Results (Top 10) ===")
        for i, provider in enumerate(providers[:10]):
            name = provider["name"]
            pct = provider["vote_power_pct"]
            capped = provider["capped_vote_power"]
            print(f"{i+1:2d}. {name:<20} {pct:>6.2f}% ({capped:,} vote power)")
        
        print(f"\n=== Comparison with Screenshot ===")
        expected = {
            "Bifrost Wallet": 3.42,
            "Flare.Space": 3.02,
            "AlphaOracle": 2.51,
            "Atlas TSO": 2.24,
            "Flare Oracle": 2.23,
            "NORTSO": 2.11
        }
        
        print("Expected vs Calculated:")
        for provider in providers[:6]:
            name = provider["name"]
            calculated = provider["vote_power_pct"]
            expected_val = expected.get(name, 0)
            diff = abs(calculated - expected_val) if expected_val > 0 else "N/A"
            status = "✅" if isinstance(diff, float) and diff < 0.5 else "❌"
            print(f"{status} {name:<20} Expected: {expected_val:>5.2f}% | Calculated: {calculated:>5.2f}% | Diff: {diff}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
