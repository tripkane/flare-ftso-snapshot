import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import types
import pytest
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

from snapshot import extract_numbers, extract_decimal, save_snapshot
import json
import datetime


def test_extract_numbers_with_commas():
    text = "Values: 1,234 and 5,678"
    assert extract_numbers(text) == ["1,234", "5,678"]


def test_extract_decimal_valid():
    assert extract_decimal("Reward: 0.05%") == "0.05"
    assert extract_decimal("Value 123.456 units") == "123.456"


def test_extract_decimal_invalid_multiple_dots():
    assert extract_decimal("invalid 1..2 value") is None


def test_save_snapshot_updates_manifest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = [{"value": 1}]
    network = "flare"

    save_snapshot(data, network=network)

    today = datetime.date.today().isoformat()
    subdir = today[:7]
    filename = f"{network}_snapshot_{today}.json"

    snap_file = tmp_path / "daily_snapshots" / subdir / filename
    docs_file = tmp_path / "docs" / "daily_snapshots" / subdir / filename
    manifest_path = tmp_path / "docs" / "daily_snapshots" / "manifest.json"

    assert snap_file.exists()
    assert docs_file.exists()

    manifest = json.loads(manifest_path.read_text())
    assert manifest[network] == [f"{subdir}/{filename}"]

    # call again to ensure manifest entry isn't duplicated
    save_snapshot(data, network=network)
    manifest = json.loads(manifest_path.read_text())
    assert manifest[network] == [f"{subdir}/{filename}"]
