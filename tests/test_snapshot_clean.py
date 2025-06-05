import os
import sys
import types
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

from snapshot import is_snapshot_relevant, clean_snapshots


def test_is_snapshot_relevant():
    schedule = [
        {"Start (UTC)": "2023-01-01 00:00:00", "End (UTC)": "2023-01-05 23:59:59"},
        {"Start (UTC)": "2023-02-01 00:00:00", "End (UTC)": "2023-02-05 23:59:59"},
    ]

    assert is_snapshot_relevant("2023-01-03", schedule)
    assert not is_snapshot_relevant("2023-03-01", schedule)


def test_clean_snapshots(tmp_path):
    schedule = [
        {"Start (UTC)": "2023-01-01 00:00:00", "End (UTC)": "2023-01-02 23:59:59"},
    ]

    relevant = tmp_path / "flare_snapshot_2023-01-01.json"
    irrelevant = tmp_path / "flare_snapshot_2023-01-03.json"
    other_file = tmp_path / "note.txt"

    for f in (relevant, irrelevant, other_file):
        f.write_text("{}")

    clean_snapshots(schedule, snapshot_dir=str(tmp_path))

    assert relevant.exists()
    assert not irrelevant.exists()
    assert other_file.exists()
