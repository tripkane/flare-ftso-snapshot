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

from snapshot import extract_numbers, extract_decimal


def test_extract_numbers_with_commas():
    text = "Values: 1,234 and 5,678"
    assert extract_numbers(text) == ["1,234", "5,678"]


def test_extract_decimal_valid():
    assert extract_decimal("Reward: 0.05%") == "0.05"
    assert extract_decimal("Value 123.456 units") == "123.456"


def test_extract_decimal_invalid_multiple_dots():
    assert extract_decimal("invalid 1..2 value") is None
