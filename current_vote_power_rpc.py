import json
import datetime
import os
import sys
import logging
from typing import Dict, List, Any, Optional

from pydantic import BaseModel

from flare_rpc_new import fetch_flare_providers_rpc, FlareRPCError
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
            # Fetch provider data via RPC instead of scraping
            providers = fetch_flare_providers_rpc(net)
                
            if not providers:
                logger.warning(f"No providers found for {net}")
                continue
                
            # Prepare data with validation
            data = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ"),
                "network": net,
                "providers": [
                    {
                        "name": p["name"], 
                        "vote_power": p.get("vote_power_pct", 0.0)
                    }
                    for p in providers
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


if __name__ == "__main__":
    net = sys.argv[1] if len(sys.argv) > 1 else None
    main(net)
