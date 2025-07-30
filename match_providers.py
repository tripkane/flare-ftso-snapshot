#!/usr/bin/env python3
"""
Manual provider name mapping based on FlareMetrics.io data
Since the website uses dynamic loading, we'll create a manual mapping
and then match it with RPC address data
"""

# Known FTSO providers from FlareMetrics.io (as of July 2025)
FLAREMETRICS_PROVIDERS = {
    # Top providers by vote power
    "Bifrost Wallet": {"rank": 1, "vote_power_pct": 3.42},
    "Flare.Space": {"rank": 2, "vote_power_pct": 3.02},
    "AlphaOracle": {"rank": 3, "vote_power_pct": 2.51},
    "Atlas TSO": {"rank": 4, "vote_power_pct": 2.24},
    "Flare Oracle": {"rank": 5, "vote_power_pct": 2.23},
    "NORTSO": {"rank": 6, "vote_power_pct": 2.11},
    "EDPFTSO": {"rank": 7, "vote_power_pct": 1.74},
    "FlareFi": {"rank": 8, "vote_power_pct": 1.71},
    "EvolveFTSO": {"rank": 9, "vote_power_pct": 1.69},
    "Solarius": {"rank": 10, "vote_power_pct": 1.61},
    "FTSO PARIS": {"rank": 11, "vote_power_pct": 1.51},
    "Flare Dienst": {"rank": 12, "vote_power_pct": 1.48},
    "Flare Beacon": {"rank": 13, "vote_power_pct": 1.33},
    "Aureus Ox": {"rank": 14, "vote_power_pct": 1.30},
    "A-FTSO": {"rank": 15, "vote_power_pct": 1.27},
    "ACDTftso": {"rank": 16, "vote_power_pct": 1.23},
    "AU": {"rank": 17, "vote_power_pct": 1.23},
    "FTSO Plus": {"rank": 18, "vote_power_pct": 1.08},
    "Oracle Daemon": {"rank": 19, "vote_power_pct": 1.05},
    "PRICEKRAKEN": {"rank": 20, "vote_power_pct": 1.01},
    "Chainbase Staking": {"rank": 21, "vote_power_pct": 0.93},
    "Bushido FTSO": {"rank": 24, "vote_power_pct": 0.85},
    "Google Cloud": {"rank": 25, "vote_power_pct": 0.77},
    "InfStones": {"rank": 26, "vote_power_pct": 0.75},
    "Aternety": {"rank": 27, "vote_power_pct": 0.69},
    "FTSO London": {"rank": 28, "vote_power_pct": 0.66},
    "AFOracle": {"rank": 29, "vote_power_pct": 0.66},
    "Ivy Oracle": {"rank": 30, "vote_power_pct": 0.63},
    "FTSOCAN": {"rank": 31, "vote_power_pct": 0.63},
    "Envision": {"rank": 32, "vote_power_pct": 0.61},
    "Use Your Spark": {"rank": 33, "vote_power_pct": 0.60},
    "WitterFTSO": {"rank": 34, "vote_power_pct": 0.50},
    "Ankr": {"rank": 36, "vote_power_pct": 0.49},
    "LightFTSO": {"rank": 37, "vote_power_pct": 0.49},
    "4DadsFTSO": {"rank": 38, "vote_power_pct": 0.48},
    "Last Oracle": {"rank": 39, "vote_power_pct": 0.47},
    "FTSO EU": {"rank": 40, "vote_power_pct": 0.44},
    "DataVector": {"rank": 41, "vote_power_pct": 0.43},
    "Ugly Kitty": {"rank": 42, "vote_power_pct": 0.39},
    "Kiln": {"rank": 43, "vote_power_pct": 0.39},
    "A41": {"rank": 44, "vote_power_pct": 0.36},
    "Knot Nodes": {"rank": 45, "vote_power_pct": 0.36},
    "Restake": {"rank": 46, "vote_power_pct": 0.35},
    "Lena Instruments": {"rank": 49, "vote_power_pct": 0.33},
    "Sun-Dara": {"rank": 51, "vote_power_pct": 0.33},
    "Scintilla": {"rank": 52, "vote_power_pct": 0.32},
    "Mickey B Fresh": {"rank": 53, "vote_power_pct": 0.30},
    "InGen.FTSO": {"rank": 54, "vote_power_pct": 0.29},
    "Flaris": {"rank": 55, "vote_power_pct": 0.29},
    "Aimlezz": {"rank": 56, "vote_power_pct": 0.28},
    "TempestFTSO": {"rank": 57, "vote_power_pct": 0.27},
    "Defi Oracles": {"rank": 59, "vote_power_pct": 0.26},
    "Xdrops Oracle": {"rank": 61, "vote_power_pct": 0.25},
    "Stakeway": {"rank": 62, "vote_power_pct": 0.25},
    "HEWG": {"rank": 64, "vote_power_pct": 0.24},
    "Comfy Nodes": {"rank": 65, "vote_power_pct": 0.24},
    "Burst FTSO": {"rank": 66, "vote_power_pct": 0.24},
    "True FTSO": {"rank": 67, "vote_power_pct": 0.23},
    "African Proofs": {"rank": 68, "vote_power_pct": 0.22},
    "FocusTSO": {"rank": 69, "vote_power_pct": 0.22},
    "FTSO UK": {"rank": 70, "vote_power_pct": 0.22},
    "uGaenn": {"rank": 71, "vote_power_pct": 0.22},
    "Wonderftso": {"rank": 72, "vote_power_pct": 0.21},
    "Tailwind FTSO": {"rank": 73, "vote_power_pct": 0.20},
    "StakeCapital FTSO": {"rank": 74, "vote_power_pct": 0.17},
    "Luganodes": {"rank": 75, "vote_power_pct": 0.17},
    "O1 FTSO": {"rank": 76, "vote_power_pct": 0.17},
    "SolidiFi FTSO": {"rank": 77, "vote_power_pct": 0.16},
    "sToadz FTSO": {"rank": 79, "vote_power_pct": 0.15},
    "Poseidon FTSO": {"rank": 80, "vote_power_pct": 0.15},
    "FlareFTSO": {"rank": 82, "vote_power_pct": 0.07},
    "FTSOExpress": {"rank": 83, "vote_power_pct": 0.05},
}

def match_providers_with_rpc_data():
    """
    Match FlareMetrics provider names with RPC address data
    """
    from flare_rpc_new import get_current_vote_power_data
    
    print("Getting current RPC provider data...")
    try:
        providers = get_current_vote_power_data("flare")
        print(f"Found {len(providers)} providers from RPC")
        
        # Create a mapping by matching vote power percentages
        matches = {}
        
        for rpc_provider in providers:
            rpc_pct = round(rpc_provider.get("vote_power_pct", 0), 2)
            rpc_address = rpc_provider.get("address", "")
            
            # Find matching provider by vote power percentage
            best_match = None
            best_diff = float('inf')
            
            for name, data in FLAREMETRICS_PROVIDERS.items():
                expected_pct = data["vote_power_pct"]
                diff = abs(rpc_pct - expected_pct)
                
                if diff < best_diff and diff < 0.1:  # Within 0.1% tolerance
                    best_diff = diff
                    best_match = name
            
            if best_match:
                matches[rpc_address.lower()] = best_match
                print(f"✓ Matched: {rpc_address} ({rpc_pct}%) -> {best_match}")
            else:
                print(f"? No match for: {rpc_address} ({rpc_pct}%)")
        
        print(f"\nMatched {len(matches)} providers out of {len(providers)}")
        
        # Save the mapping
        import json
        with open('matched_providers.json', 'w') as f:
            json.dump(matches, f, indent=2)
        
        print("Saved matched providers to matched_providers.json")
        return matches
        
    except Exception as e:
        print(f"Error: {e}")
        return {}

def update_provider_names_cache():
    """
    Update the provider names cache with matched data
    """
    matches = match_providers_with_rpc_data()
    
    if matches:
        # Update the provider_names.json file
        import json
        import os
        
        cache_file = "provider_names.json"
        
        # Load existing cache
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                existing = json.load(f)
        else:
            existing = {}
        
        # Merge with new matches
        existing.update(matches)
        
        # Save updated cache
        with open(cache_file, 'w') as f:
            json.dump(existing, f, indent=2)
        
        print(f"Updated provider names cache with {len(matches)} new mappings")
        print(f"Total cached provider names: {len(existing)}")

if __name__ == "__main__":
    update_provider_names_cache()
