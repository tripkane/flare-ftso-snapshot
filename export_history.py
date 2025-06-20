import json
import os
from flare_rpc import connect, get_all_delegation_logs


def main(network: str = "flare") -> None:
    w3 = connect()
    logs = get_all_delegation_logs(w3)
    out_dir = os.path.join("history")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{network}_delegations.json")
    # convert to plain dicts to avoid serialization issues
    serializable = [{k: log[k] for k in log} for log in logs]
    with open(path, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"Saved {len(serializable)} logs to {path}")


if __name__ == "__main__":
    main()
