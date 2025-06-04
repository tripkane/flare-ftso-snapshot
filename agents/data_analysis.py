
def analyze_snapshot(snapshot):
    results = []
    for provider in snapshot.get("providers", []):
        # `snapshot.py` stores the key as `reward_rate`, so use the same
        # naming here for analysis. Using the wrong key would cause all
        # reward rates to default to 0 and skip important checks.
        reward_rate = provider.get("reward_rate", 0)
        if reward_rate < 0.5:
            results.append({"provider": provider["name"], "status": "Low reward rate", "rate": reward_rate})
        elif reward_rate > 2.5:
            results.append({"provider": provider["name"], "status": "Risk of penalty", "rate": reward_rate})
    return results
