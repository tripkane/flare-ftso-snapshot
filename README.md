# flare-ftso-snapshot
This repo is designed to scrape the FTSO provider rewards data and associated registration information on a daily timeframe so one can make informed decisions about which FTSO providers over times are the best to choose to maximise reward rates and reduce network fees associated with swapping delegations too often

## Querying snapshots with an LLM

Run a small API to query the snapshot data using a lightweight language model.

### Setup

```bash
pip install -r requirements.txt
```

### Start the server

```bash
uvicorn query_server:app --reload
```

Then open the dashboard (served from `docs/`) in a browser. A prompt bar in the top right sends questions to `http://localhost:8000/query` and displays the answer.
