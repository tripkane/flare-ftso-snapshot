import os
from typing import List, Optional, Any

try:
    from web3 import Web3
except Exception:  # pragma: no cover - allow running without web3 installed
    import types, hashlib

    class _DummyEth:
        def contract(self, *_, **__):
            raise NotImplementedError

        def get_logs(self, *_args, **_kwargs):
            raise NotImplementedError

    class Web3:
        def __init__(self, provider=None):
            self.eth = _DummyEth()

        class HTTPProvider:  # type: ignore
            def __init__(self, url):
                self.url = url

        @staticmethod
        def keccak(text=""):
            return hashlib.sha3_256(text.encode()).digest()

        @staticmethod
        def to_checksum_address(addr):
            return addr

        @staticmethod
        def to_bytes(hexstr="0x"):
            return bytes.fromhex(hexstr[2:])

        @staticmethod
        def to_hex(value: bytes):
            return "0x" + value.hex()

# Default Flare RPC endpoint. This can be overridden with the FLARE_RPC_URL env var
DEFAULT_RPC_URL = "https://flare-api.flare.network/ext/C/rpc"

# Contract addresses are network constants. These defaults match the main Flare network.
FTSO_REGISTRY_ADDRESS = Web3.to_checksum_address("0x1000000000000000000000000000000000000003")
FTSO_MANAGER_ADDRESS = Web3.to_checksum_address("0x1000000000000000000000000000000000000004")

# Minimal ABI fragments needed for our queries
FTSO_REGISTRY_ABI = [
    {
        "name": "getProviders",
        "outputs": [{"name": "", "type": "address[]"}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "getProviderByIndex",
        "outputs": [{"name": "", "type": "address"}],
        "inputs": [{"name": "index", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

FTSO_MANAGER_ABI = [
    {
        "name": "getEpochData",
        "outputs": [
            {"name": "_startBlock", "type": "uint256"},
            {"name": "_endBlock", "type": "uint256"},
            {"name": "_totalReward", "type": "uint256"},
        ],
        "inputs": [{"name": "_epochId", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# Event signatures for delegation events
DELEGATED_TOPIC = Web3.keccak(text="VotingPowerDelegated(address,address,uint256)").hex()
UNDELEGATED_TOPIC = Web3.keccak(text="VotingPowerUndelegated(address,address,uint256)").hex()


def connect(url: Optional[str] = None) -> Web3:
    """Return a Web3 connection to the Flare RPC endpoint."""
    rpc = url or os.getenv("FLARE_RPC_URL", DEFAULT_RPC_URL)
    return Web3(Web3.HTTPProvider(rpc))


def list_providers(w3: Web3) -> List[str]:
    """Return the list of registered provider addresses."""
    registry = w3.eth.contract(address=FTSO_REGISTRY_ADDRESS, abi=FTSO_REGISTRY_ABI)
    try:
        return registry.functions.getProviders().call()
    except Exception:
        # Fallback to getProviderByIndex if getProviders not available
        length = 0
        try:
            length = registry.functions.getProvidersLength().call()
        except Exception:
            pass
        providers = []
        for i in range(length):
            providers.append(registry.functions.getProviderByIndex(i).call())
        return providers


def query_epoch_data(w3: Web3, epoch_id: int) -> Any:
    """Return basic epoch data from the FTSO manager."""
    manager = w3.eth.contract(address=FTSO_MANAGER_ADDRESS, abi=FTSO_MANAGER_ABI)
    return manager.functions.getEpochData(epoch_id).call()


def delegation_logs(
    w3: Web3,
    from_block: int,
    to_block: int,
    provider: Optional[str] = None,
    include_undelegations: bool = True,
) -> List[Any]:
    """Return delegation and undelegation logs in the block range."""
    topics: List[Any]
    if include_undelegations:
        topics = [[DELEGATED_TOPIC, UNDELEGATED_TOPIC]]
    else:
        topics = [DELEGATED_TOPIC]
    if provider:
        topics.append(w3.to_hex(w3.to_bytes(hexstr=provider).rjust(32, b"\x00")))

    return w3.eth.get_logs(
        {
            "fromBlock": from_block,
            "toBlock": to_block,
            "topics": topics,
        }
    )


def get_all_delegation_logs(
    w3: Web3,
    provider: Optional[str] = None,
    chunk_size: int = 50000,
    include_undelegations: bool = True,
) -> List[Any]:
    """Return delegation logs from block 0 to the latest block."""
    latest = w3.eth.block_number
    logs: List[Any] = []
    start = 0
    while start <= latest:
        end = min(start + chunk_size - 1, latest)
        logs.extend(
            delegation_logs(
                w3, start, end, provider=provider, include_undelegations=include_undelegations
            )
        )
        start = end + 1
    return logs
