
def analyze_snapshot(snapshot):
    results = []
    for provider in snapshot.get("providers", []):
        reward_rate = provider.get("rewardRate", 0)
        if reward_rate < 0.5:
            results.append({"provider": provider["name"], "status": "Low reward rate", "rate": reward_rate})
        elif reward_rate > 2.5:
            results.append({"provider": provider["name"], "status": "Risk of penalty", "rate": reward_rate})
    return results
