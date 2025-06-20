# flare-ftso-snapshot
This project collects FTSO provider data directly from the Flare blockchain. Snapshots are taken at each reward epoch so delegators can analyse provider performance without relying on third party websites.

## Viewing the dashboard

Open `docs/index.html` directly in your browser or visit the published GitHub
Pages site at `https://tripkane.github.io/flare-ftso-snapshot/`. The dashboard
fetches all snapshot JSON files from GitHub so no local server is required.

### Enabling GitHub Pages

The workflow in `.github/workflows/pages.yml` deploys the `docs/` folder using
GitHub Actions. If deployment fails with a `404` error, ensure Pages are enabled
for the repository:

1. Navigate to **Settings → Pages** in the repository UI.
2. Under **Build and deployment**, choose **GitHub Actions** as the source.
3. Save the configuration and re-run the `GitHub Pages` workflow.

Once enabled, every push to the `main` branch will update the site automatically.

## Querying snapshots with an LLM (optional)

An optional FastAPI server provides an endpoint for LLM powered questions about
the dataset.

### Setup
This project requires **Python 3.10**. It is recommended to create a virtual
environment before installing dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
This installs all dependencies required to run the snapshot scripts which now
connect directly to a Flare RPC node. Set the `FLARE_RPC_URL` environment
variable if you want to use a custom endpoint.

### Start the server (optional)

```bash
uvicorn query_server:app --reload
```


If you want to experiment with the LLM query endpoint, run the server and visit
`http://localhost:8000`. The dashboard will be served locally and the prompt bar
sends questions to `http://localhost:8000/query`.

### Ask the data on GitHub Pages

For a quick demo without running a server, open `docs/qna.html`. This page
loads `docs/data.json` and sends your questions directly to GitHub's models API.
Create a `docs/config.js` file (do **not** commit it) with a fine-grained token:

```js
window.GITHUB_TOKEN = "ghp_...";
```

When the file is present locally or uploaded via the GitHub Pages UI, you can
query the dataset straight from the browser.


## Running Tests

Execute the test suite with `pytest`:

```bash
pytest
```

## Automated Vote Power Snapshots

GitHub Actions runs `current_vote_power.py` every ten minutes. This process keeps
`current_vote_power/` and `docs/current_vote_power/` updated with the latest Flare
and Songbird vote-power data. Files are stored in `YYYY-MM` subfolders to avoid
exceeding GitHub's 1000 file limit in a single directory.

## Cleaning Snapshot Directories

To remove snapshot files that are not aligned with epoch start dates, run
`clean_snapshots.py` and optionally pass the directory you want to clean:

```bash
python clean_snapshots.py docs/daily_snapshots
```

Without an argument it cleans `daily_snapshots/` in the project root. This can
be used after running the workflow manually if you need to tidy the `docs`
folder. The scheduled snapshot workflow also runs this script to keep
`daily_snapshots/` and `docs/daily_snapshots/` free of stray files. Snapshot
files now live in monthly subdirectories (e.g. `2025-06/`), so cleaning will
also traverse these folders.

## Exporting Delegation History

Use `export_history.py` to fetch all delegation events from block `0` onwards.
The script queries the configured RPC endpoint and stores the logs in
`history/<network>_delegations.json`.

```bash
python export_history.py    # uses FLARE_RPC_URL if set
```

This dataset can be used for deeper analysis of vote power changes over time.

## License

This project is licensed under the [MIT License](LICENSE).


