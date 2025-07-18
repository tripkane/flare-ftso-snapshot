import os
import sys
import json
import types
import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Stub selenium and bs4 modules to allow importing snapshot without dependencies
selenium = types.ModuleType("selenium")
webdriver = types.ModuleType("selenium.webdriver")
chrome = types.ModuleType("selenium.webdriver.chrome")
options_module = types.ModuleType("selenium.webdriver.chrome.options")
options_module.Options = object
service_module = types.ModuleType("selenium.webdriver.chrome.service")
service_module.Service = object

selenium.webdriver = webdriver
webdriver.chrome = chrome
chrome.options = options_module
chrome.service = service_module

sys.modules.setdefault("selenium", selenium)
sys.modules.setdefault("selenium.webdriver", webdriver)
sys.modules.setdefault("selenium.webdriver.chrome", chrome)
sys.modules.setdefault("selenium.webdriver.chrome.options", options_module)
sys.modules.setdefault("selenium.webdriver.chrome.service", service_module)

bs4_module = types.ModuleType("bs4")
bs4_module.BeautifulSoup = object
sys.modules.setdefault("bs4", bs4_module)

from snapshot import (
    is_snapshot_relevant,
    clean_snapshots,
    is_current_time_epoch_start,
    should_run_snapshot,
)


def test_is_snapshot_relevant():
    schedule = [
        {"Start (UTC)": "2023-01-01 00:00:00", "End (UTC)": "2023-01-05 23:59:59"},
        {"Start (UTC)": "2023-02-01 00:00:00", "End (UTC)": "2023-02-05 23:59:59"},
    ]

    assert is_snapshot_relevant("2023-01-01", schedule)
    assert not is_snapshot_relevant("2023-01-03", schedule)
    assert not is_snapshot_relevant("2023-03-01", schedule)


def test_clean_snapshots(tmp_path):
    schedule = [
        {"Start (UTC)": "2023-01-01 00:00:00", "End (UTC)": "2023-01-02 23:59:59"},
    ]
    snap_dir = tmp_path / "snaps"
    docs_dir = tmp_path / "docs"
    snap_dir.mkdir()
    docs_dir.mkdir(parents=True)

    relevant = snap_dir / "flare_snapshot_2023-01-01.json"
    irrelevant = snap_dir / "flare_snapshot_2023-01-03.json"
    other_file = snap_dir / "note.txt"

    for f in (relevant, irrelevant, other_file):
        f.write_text("{}")

    # mirror files in docs directory
    for f in (relevant, irrelevant):
        (docs_dir / f.name).write_text("{}")

    manifest_path = docs_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps({"flare": [relevant.name, irrelevant.name], "songbird": []})
    )

    clean_snapshots(
        schedule,
        snapshot_dir=str(snap_dir),
        docs_dir=str(docs_dir),
        manifest_path=str(manifest_path),
        network="flare",
    )

    assert relevant.exists()
    assert not irrelevant.exists()
    assert other_file.exists()
    assert (docs_dir / relevant.name).exists()
    assert not (docs_dir / irrelevant.name).exists()

    manifest = json.loads(manifest_path.read_text())
    assert manifest["flare"] == [relevant.name]


def test_is_current_time_epoch_start():
    schedule = [
        {"Start (UTC)": "2023-01-01 07:10:00"},
        {"Start (UTC)": "2023-01-01 19:10:00"},
    ]

    # within the 30 minute default window
    near = datetime.datetime(2023, 1, 1, 7, 25)
    assert is_current_time_epoch_start(schedule, near)

    # outside the window
    later = datetime.datetime(2023, 1, 1, 8, 0)
    assert not is_current_time_epoch_start(schedule, later)


def test_should_run_snapshot_when_missing(tmp_path, monkeypatch):
    schedule = [{"Start (UTC)": "2023-01-01 07:10:00"}]
    now = datetime.datetime(2023, 1, 1, 8, 0)
    monkeypatch.chdir(tmp_path)
    assert should_run_snapshot(schedule, "flare", now)


def test_should_run_snapshot_skips_when_exists(tmp_path, monkeypatch):
    schedule = [{"Start (UTC)": "2023-01-01 07:10:00"}]
    now = datetime.datetime(2023, 1, 1, 8, 0)
    monkeypatch.chdir(tmp_path)
    os.makedirs("daily_snapshots/2023-01", exist_ok=True)
    open("daily_snapshots/2023-01/flare_snapshot_2023-01-01.json", "w").write("{}")
    assert not should_run_snapshot(schedule, "flare", now)

