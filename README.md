# flare-ftso-snapshot
This repo is designed to scrape the FTSO provider rewards data and associated registration information on a daily timeframe so one can make informed decisions about which FTSO providers over times are the best to choose to maximise reward rates and reduce network fees associated with swapping delegations too often

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
This installs all dependencies required to run the snapshot scripts,
including `selenium` and `beautifulsoup4` for web scraping.

The scraper expects `chromium-browser` and `chromedriver` to be installed.
If they are located in non‑standard paths, set the `CHROMIUM_BINARY` and
`CHROMEDRIVER` environment variables before running any snapshot scripts, e.g.:

```bash
export CHROMIUM_BINARY=/path/to/chromium
export CHROMEDRIVER=/path/to/chromedriver
```

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

## License

This project is licensed under the [MIT License](LICENSE).


