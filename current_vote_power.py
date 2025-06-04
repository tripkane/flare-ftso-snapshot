import json
import datetime
import os
import sys

from snapshot import init_driver, scrape_flaremetrics


def save_current_vote_power(data, network="flare"):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = os.path.join("current_vote_power")
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{network}_vp_{ts}.json"
    path = os.path.join(out_dir, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved current vote power: {path}")
    docs_dir = os.path.join("docs", "current_vote_power")
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, filename), "w") as f:
        json.dump(data, f, indent=2)
    update_manifest(docs_dir, filename, network)


def update_manifest(docs_dir, filename, network):
    manifest_path = os.path.join(docs_dir, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        manifest = {"flare": [], "songbird": []}
    manifest.setdefault(network, [])
    manifest[network].append(filename)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def main(network=None):
    if network in ("flare", "songbird"):
        networks = [network]
    else:
        networks = ["flare", "songbird"]

    for net in networks:
        driver = init_driver()
        try:
            providers = scrape_flaremetrics(driver, net)
        finally:
            driver.quit()

        data = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "providers": [
                {"name": p["name"], "vote_power_pct": p.get("vote_power_pct", 0.0)}
                for p in providers
            ],
        }
        save_current_vote_power(data, net)


if __name__ == "__main__":
    net = sys.argv[1] if len(sys.argv) > 1 else None
    main(net)
