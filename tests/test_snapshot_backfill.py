import os
import sys
import json
import types
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Stub selenium and bs4 so snapshot imports succeed
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

import snapshot


def test_save_snapshot_custom_date(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = [{"value": 1}]
    snapshot_date = "2023-01-01"
    network = "flare"

    snapshot.save_snapshot(data, network=network, snapshot_date=snapshot_date)

    subdir = snapshot_date[:7]
    filename = f"{network}_snapshot_{snapshot_date}.json"
    snap_file = tmp_path / "daily_snapshots" / subdir / filename
    docs_file = tmp_path / "docs" / "daily_snapshots" / subdir / filename
    manifest_path = tmp_path / "docs" / "daily_snapshots" / "manifest.json"

    assert snap_file.exists()
    assert docs_file.exists()

    manifest = json.loads(manifest_path.read_text())
    assert manifest[network] == [f"{subdir}/{filename}"]


def test_check_for_missing_snapshots(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    schedule = [
        {"Start (UTC)": "2023-01-01 00:00:00"},
        {"Start (UTC)": "2023-01-02 00:00:00"},
    ]

    class FixedDate(datetime.date):
        @classmethod
        def today(cls):
            return cls(2023, 1, 2)

    monkeypatch.setattr(snapshot.datetime, "date", FixedDate)
    monkeypatch.setattr(snapshot, "scrape_with_retries", lambda network: [{"v": 1}])

    snapshot.check_for_missing_snapshots(schedule, network="flare")

    for d in ["2023-01-01", "2023-01-02"]:
        subdir = d[:7]
        filename = f"flare_snapshot_{d}.json"
        assert (tmp_path / "daily_snapshots" / subdir / filename).exists()
