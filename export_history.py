import json
import os
import re
import requests
from requests.exceptions import JSONDecodeError, HTTPError
from html import unescape
from flare_rpc import connect, get_all_delegation_logs

DEFAULT_GRAPHQL_URL = "https://flare-explorer.flare.network/graphql"

QUERY = """
query($first: Int!, $skip: Int!) {
  delegationChangedEvents(first: $first, skip: $skip) {
    id
    delegator
    delegatee
    amount
    blockNumber
    transactionHash
  }
}
"""


def fetch_all_delegations_graphql(url: str, first: int = 1000) -> list:
    """Fetch all delegation change events via GraphQL."""
    delegations = []
    skip = 0
    while True:
        payload = {"query": QUERY, "variables": {"first": first, "skip": skip}}
        resp = requests.post(url, json=payload, timeout=30)
        try:
            resp.raise_for_status()
        except HTTPError as exc:
            if resp.status_code == 404 and url.endswith("/graphql"):
                alt = url[:-len("graphql")] + "graphiql"
                print(f"{url} returned 404, retrying {alt}")
                url = alt
                resp = requests.post(url, json=payload, timeout=30)
                resp.raise_for_status()
            else:
                raise
        try:
            json_resp = resp.json()
        except JSONDecodeError as exc:
            snippet = resp.text[:200]
            raise RuntimeError(f"Failed to decode JSON from {url}: {snippet!r}") from exc
        data = json_resp.get("data", {}).get("delegationChangedEvents", [])
        if not data:
            break
        delegations.extend(data)
        skip += first
    return delegations


def fetch_delegations_rpc() -> list:
    """Fetch delegation change logs via RPC as a fallback."""
    w3 = connect()
    logs = get_all_delegation_logs(w3)
    return [{k: log[k] for k in log} for log in logs]


def scrape_delegations_flaremetrics(network: str = "flare") -> list:
    """Scrape delegation events from flaremetrics.io."""
    url = f"https://flaremetrics.io/{network}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    html = resp.text
    rows = []
    for row_html in re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL):
        cols = re.findall(r"<td.*?>(.*?)</td>", row_html, re.DOTALL)
        rows.append([unescape(re.sub("<.*?>", "", c)).strip() for c in cols])

    delegations = []
    for cols in rows:
        if len(cols) >= 5:
            delegations.append(
                {
                    "delegator": cols[0],
                    "delegatee": cols[1],
                    "amount": cols[2],
                    "blockNumber": cols[3],
                    "transactionHash": cols[4],
                }
            )
    return delegations


def fetch_all_delegations(url: str, first: int = 1000, network: str = "flare") -> list:
    """Fetch delegation events with multiple fallbacks."""
    try:
        return fetch_all_delegations_graphql(url, first=first)
    except Exception as exc:
        print(f"GraphQL fetch failed: {exc}; trying flaremetrics")
        try:
            return scrape_delegations_flaremetrics(network)
        except Exception as exc2:
            print(f"Flaremetrics scrape failed: {exc2}; falling back to RPC")
            return fetch_delegations_rpc()


def main(network: str = "flare") -> None:
    url = os.getenv("FLARE_GRAPHQL_URL", DEFAULT_GRAPHQL_URL)
    if url.endswith("/graphiql"):
        url = url[: -len("graphiql")] + "graphql"
    print(f"Using GraphQL endpoint: {url}")
    logs = fetch_all_delegations(url, network=network)
    out_dir = os.path.join("history")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{network}_delegations.json")
    with open(path, "w") as f:
        json.dump(logs, f, indent=2)
    print(f"Saved {len(logs)} logs to {path}")


if __name__ == "__main__":
    main()
