import sys
import types
import json
import pytest

# Create a stub requests module so export_history imports it
requests = types.ModuleType("requests")
class DummyJSONDecodeError(Exception):
    pass
exceptions_module = types.ModuleType("requests.exceptions")
exceptions_module.JSONDecodeError = DummyJSONDecodeError
class DummyHTTPError(Exception):
    pass
exceptions_module.HTTPError = DummyHTTPError
requests.exceptions = exceptions_module
requests.post = lambda *a, **k: None
sys.modules.setdefault("requests", requests)
sys.modules.setdefault("requests.exceptions", exceptions_module)

import export_history

class DummyResponse:
    def __init__(self, text="bad", status_code=200):
        self.text = text
        self.status_code = status_code
    def raise_for_status(self):
        if self.status_code >= 400:
            raise export_history.requests.exceptions.HTTPError()
    def json(self):
        if self.text.startswith("{"):
            return json.loads(self.text)
        raise DummyJSONDecodeError("bad")


def test_fetch_all_delegations_bad_json(monkeypatch):
    def fake_post(url, json=None, timeout=0):
        return DummyResponse("<html>error</html>")
    monkeypatch.setattr(export_history.requests, "post", fake_post)
    with pytest.raises(RuntimeError):
        export_history.fetch_all_delegations("http://example.com")


def test_fallback_to_graphiql(monkeypatch):
    calls = []

    def fake_post(url, json=None, timeout=0):
        calls.append(url)
        if url.endswith("/graphql"):
            return DummyResponse("not found", status_code=404)
        return DummyResponse('{"data":{"delegationChangedEvents":[]}}', status_code=200)

    monkeypatch.setattr(export_history.requests, "post", fake_post)
    result = export_history.fetch_all_delegations("http://example.com/graphql", first=1)
    assert result == []
    assert calls == ["http://example.com/graphql", "http://example.com/graphiql"]
