import sys
import types
import pytest

# Create a stub requests module so export_history imports it
requests = types.ModuleType("requests")
class DummyJSONDecodeError(Exception):
    pass
exceptions_module = types.ModuleType("requests.exceptions")
exceptions_module.JSONDecodeError = DummyJSONDecodeError
requests.exceptions = exceptions_module
requests.post = lambda *a, **k: None
sys.modules.setdefault("requests", requests)
sys.modules.setdefault("requests.exceptions", exceptions_module)

import export_history

class DummyResponse:
    def __init__(self, text="bad"):
        self.text = text
    def raise_for_status(self):
        pass
    def json(self):
        raise DummyJSONDecodeError("bad")


def test_fetch_all_delegations_bad_json(monkeypatch):
    def fake_post(url, json=None, timeout=0):
        return DummyResponse("<html>error</html>")
    monkeypatch.setattr(export_history.requests, "post", fake_post)
    with pytest.raises(RuntimeError):
        export_history.fetch_all_delegations("http://example.com")
