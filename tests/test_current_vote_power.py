import os
import sys
import json
import types
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Stub selenium and bs4 modules so snapshot import works
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

import current_vote_power

class FixedDatetime(datetime.datetime):
    @classmethod
    def utcnow(cls):
        return cls(2023, 1, 1, 0, 0, 0)


def test_save_current_vote_power_manifest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(current_vote_power.datetime, "datetime", FixedDatetime)

    data = {"value": 1}
    network = "flare"

    current_vote_power.save_current_vote_power(data, network=network)
    current_vote_power.save_current_vote_power(data, network=network)

    ts = FixedDatetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    filename = f"{network}_vp_{ts}.json"

    manifest_path = tmp_path / "docs" / "current_vote_power" / "manifest.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text())
    assert manifest[network] == [filename]


def test_save_current_vote_power_with_pydantic(tmp_path, monkeypatch):
    """Ensure Pydantic SnapshotData can be saved without errors."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(current_vote_power.datetime, "datetime", FixedDatetime)

    data = {
        "timestamp": FixedDatetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ"),
        "network": "flare",
        "providers": [{"name": "A", "vote_power": 1.0}],
    }
    snap = current_vote_power.validate_snapshot_data(data)
    current_vote_power.save_current_vote_power(snap, network="flare")

    ts = FixedDatetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    file_path = tmp_path / "current_vote_power" / f"flare_vp_{ts}.json"
    assert file_path.exists()
