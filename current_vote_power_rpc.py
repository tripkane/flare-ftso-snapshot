import json
import datetime
import os
import sys
import logging
from typing import Dict, List, Any, Optional

from pydantic import BaseModel

from flare_rpc_new import fetch_flare_providers_rpc, FlareRPCError, make_rpc_call, get_contract_address, encode_string_param
from schemas import validate_snapshot_data, sanitize_file_path
from exceptions import FileOperationError, DataValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _to_serializable(obj):
    """Return JSON-serializable data from a Pydantic model or plain object."""
    if isinstance(obj, BaseModel):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return obj.dict()
    return obj


def save_current_vote_power(data, network="flare"):
    """Save current vote power data to files"""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = os.path.join("current_vote_power")
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{network}_vp_{ts}.json"
    path = os.path.join(out_dir, filename)
    serializable = _to_serializable(data)
    with open(path, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"Saved current vote power: {path}")
    docs_dir = os.path.join("docs", "current_vote_power")
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, filename), "w") as f:
        json.dump(serializable, f, indent=2)
    update_manifest(docs_dir, filename, network)


def update_manifest(docs_dir, filename, network):
    """Update the manifest file with new snapshot"""
    manifest_path = os.path.join(docs_dir, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        manifest = {"flare": [], "songbird": []}
    manifest.setdefault(network, [])
    if filename not in manifest[network]:
        manifest[network].append(filename)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def fetch_accurate_vote_power_from_blockchain(network: str) -> List[Dict[str, Any]]:
    """
    Fetch accurate FTSO vote power data directly from blockchain using vote power events.
    
    This extracts real-time vote power data from the VotePowerContract events,
    providing the actual vote power values used in FTSO calculations.
    
    The events come from contract 0x1000000000000000000000000000000000000002
    with signature 0xe7aa66356adbd5e839ef210626f6d8f6f72109c17fadf4c4f9ca82b315ae79b4
    
    Args:
        network: 'flare' or 'songbird'
        
    Returns:
        List of providers with accurate vote power data from blockchain events
    """
    logger.info(f"Fetching accurate vote power data from blockchain events for {network}")
    
    try:
        # Use the VotePowerContract (0x1000000000000000000000000000000000000002) 
        # to get vote power events which contain the real-time vote power data
        vote_power_contract = "0x1000000000000000000000000000000000000002"
        vote_power_event_sig = "0xe7aa66356adbd5e839ef210626f6d8f6f72109c17fadf4c4f9ca82b315ae79b4"
        
        # Get current block number
        current_block_result = make_rpc_call(network, "eth_blockNumber", [])
        current_block = int(current_block_result, 16)
        
        # Look for events in recent blocks (last 1000 blocks to get current state)
        from_block = hex(current_block - 1000)
        to_block = "latest"
        
        logger.info(f"Searching for vote power events from block {from_block} to {to_block}")
        
        # Get vote power events
        events_result = make_rpc_call(
            network,
            "eth_getLogs",
            [{
                "address": vote_power_contract,
                "topics": [vote_power_event_sig],
                "fromBlock": from_block,
                "toBlock": to_block
            }]
        )
        
        if not events_result:
            raise FlareRPCError(f"No vote power events found for {network}")
        
        logger.info(f"Found {len(events_result)} vote power events")
        
        # Process events to extract provider vote power data
        provider_vote_powers = {}
        
        for event in events_result:
            try:
                # Event data format: provider_address (32 bytes) + vote_power (32 bytes)
                data = event["data"]
                if len(data) >= 130:  # 0x + 128 hex chars (64 bytes)
                    # Extract provider address (first 32 bytes, take last 20 bytes for address)
                    provider_hex = data[2 + 24:2 + 64]  # Skip 0x and 12 zero bytes
                    provider_address = "0x" + provider_hex
                    
                    # Extract vote power (second 32 bytes)
                    vote_power_hex = data[66:130]  # Next 32 bytes
                    vote_power = int(vote_power_hex, 16)
                    
                    # Store the latest vote power for each provider
                    provider_vote_powers[provider_address] = vote_power
                    
            except Exception as e:
                logger.debug(f"Error processing event: {e}")
                continue
        
        if not provider_vote_powers:
            raise FlareRPCError(f"No valid vote power data extracted from events for {network}")
        
        # Calculate total vote power
        total_vote_power = sum(provider_vote_powers.values())
        
        # Convert to providers list with percentages
        providers = []
        for address, vote_power in provider_vote_powers.items():
            if total_vote_power > 0:
                vote_power_pct = (vote_power / total_vote_power) * 100
            else:
                vote_power_pct = 0
                
            # Get provider name
            provider_name = get_provider_name_for_address(address, network)
            
            providers.append({
                "name": provider_name,
                "address": address,
                "raw_vote_power": vote_power,
                "vote_power_pct": round(vote_power_pct, 4),
            })
        
        # Sort by vote power percentage
        providers.sort(key=lambda x: x["vote_power_pct"], reverse=True)
        
        logger.info(f"Successfully extracted vote power for {len(providers)} providers from blockchain events")
        return providers
        
    except Exception as e:
        logger.error(f"Error fetching accurate vote power from blockchain: {e}")
        raise FlareRPCError(f"Failed to fetch vote power from blockchain events: {e}")


def get_provider_name_for_address(address: str, network: str) -> str:
    """
    Get provider name for a voter address using known FTSO provider mapping.
    
    Args:
        address: Voter address
        network: Network name
        
    Returns:
        Provider name or formatted address
    """
    # Known FTSO provider addresses from blockchain analysis
    provider_mapping = {
        "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c": "Bifrost Wallet",
        "0x7b61f9f27153a4f2f57dc30bf08a8eb0ccb96c22": "Flare.Space", 
        "0xbce1972de5d1598a948a36186ecebfd4690f3a5c": "AlphaOracle",
        "0x9c7a4c83842b29bb4a082b0e689cb9474bd938d0": "Flare Oracle",
        "0x89e50dc0380e597ece79c8494baafd84537ad0d4": "Atlas TSO",
        "0xdbf71d7840934eb82fa10173103d4e9fd4054dd1": "NORTSO",
    }
    
    address_lower = address.lower()
    return provider_mapping.get(address_lower, f"Provider_{address[:8]}...{address[-6:]}")


def main(network: Optional[str] = None) -> None:
    """
    Main function to collect current vote power data via RPC.
    
    Args:
        network: Network to collect data for ('flare', 'songbird', or None for both)
    """
    if network in ("flare", "songbird"):
        networks = [network]
    else:
        networks = ["flare", "songbird"]

    for net in networks:
        logger.info(f"Starting vote power collection for {net} via RPC")
        
        try:
            # Use accurate blockchain method with vote power events instead of wrong data source
            logger.info(f"Fetching accurate vote power data from blockchain events for {net}")
            providers = fetch_accurate_vote_power_from_blockchain(net)
                
            if not providers:
                logger.warning(f"No providers found for {net}")
                continue
            
            # Apply FTSO vote power cap (2.5% per provider)
            # This is crucial for accurate FTSO calculations
            capped_providers = apply_ftso_vote_power_cap(providers)
                
            # Prepare data with validation
            data = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ"),
                "network": net,
                "providers": [
                    {
                        "name": p["name"], 
                        "vote_power": p.get("vote_power_pct", 0.0),
                        "capped_vote_power": p.get("capped_vote_power", 0.0),
                        "original_vote_power": p.get("original_vote_power_pct", 0.0)
                    }
                    for p in capped_providers
                ],
            }
            
            # Validate data before saving
            try:
                validated_data = validate_snapshot_data(data)
                logger.info(f"Data validation successful for {net}")
            except Exception as e:
                logger.error(f"Data validation failed for {net}: {e}")
                # Continue with unvalidated data but log the issue
                validated_data = data
            
            save_current_vote_power(validated_data, net)
            logger.info(f"Successfully collected vote power data for {net} via RPC")
            
        except FlareRPCError as e:
            logger.error(f"RPC error for {net}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error collecting data for {net}: {e}")
            continue


def apply_ftso_vote_power_cap(providers: List[Dict[str, Any]], cap_percentage: float = 2.5) -> List[Dict[str, Any]]:
    """
    Apply FTSO vote power cap (2.5%) as per STP.01 governance proposal.
    
    This is essential for accurate FTSO calculations as providers are capped
    at 2.5% of total vote power to ensure decentralization.
    """
    if not providers:
        return []
    
    # Calculate total vote power before capping
    total_original = sum(p.get("vote_power_pct", 0) for p in providers)
    
    capped_providers = []
    total_after_cap = 0
    
    for provider in providers:
        original_pct = provider.get("vote_power_pct", 0)
        
        # Apply 2.5% cap
        capped_pct = min(original_pct, cap_percentage)
        total_after_cap += capped_pct
        
        # Keep original data and add capped values
        capped_provider = provider.copy()
        capped_provider["original_vote_power_pct"] = original_pct
        capped_provider["capped_vote_power"] = capped_pct
        capped_provider["was_capped"] = original_pct > cap_percentage
        
        capped_providers.append(capped_provider)
    
    # Recalculate percentages based on capped total
    if total_after_cap > 0:
        for provider in capped_providers:
            capped_vote_power = provider["capped_vote_power"]
            final_percentage = (capped_vote_power / total_after_cap) * 100
            provider["vote_power_pct"] = round(final_percentage, 2)
    
    # Sort by final percentage
    capped_providers.sort(key=lambda x: x["vote_power_pct"], reverse=True)
    
    logger.info(f"Applied 2.5% vote power cap. Original total: {total_original:.2f}%, After cap: {total_after_cap:.2f}%")
    
    return capped_providers


if __name__ == "__main__":
    net = sys.argv[1] if len(sys.argv) > 1 else None
    main(net)
