# flare-ftso-snapshot
This repo is designed to scrape the FTSO provider rewards data and associated registration information on a daily timeframe so one can make informed decisions about which FTSO providers over times are the best to choose to maximise reward rates and reduce network fees associated with swapping delegations too often

## Querying snapshots with an LLM

Run a small API to query the snapshot data using a lightweight language model.

### Setup
This project requires **Python 3.11**. It is recommended to create a virtual
environment before installing dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Start the server

```bash
uvicorn query_server:app --reload
```


Start the server and visit `http://localhost:8000` in your browser. The dashboard
is served directly by the API and the prompt bar sends questions to
`http://localhost:8000/query`.


## Running Tests

Execute the test suite with `pytest`:

```bash
pytest
```

## Automated Vote Power Snapshots

GitHub Actions runs `current_vote_power.py` every ten minutes. This process keeps `current_vote_power/` and `docs/current_vote_power/` updated with the latest Flare and Songbird vote-power data.
## License

This project is licensed under the [MIT License](LICENSE).


