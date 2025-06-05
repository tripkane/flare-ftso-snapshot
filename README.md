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


Start the server and visit `http://localhost:8000` in your browser. The dashboard
is served directly by the API and the prompt bar sends questions to
`http://localhost:8000/query`.

## License

This project is licensed under the [MIT License](LICENSE).

