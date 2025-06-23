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
requests.get = lambda *a, **k: None
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


def test_fetch_all_delegations_bad_json_scrape(monkeypatch):
    def fake_post(url, json=None, timeout=0):
        return DummyResponse("<html>error</html>")

    html = (
        "<table><tbody><tr><td>a</td><td>b</td><td>1</td><td>2</td><td>h</td></tr></tbody></table>"
    )

    monkeypatch.setattr(export_history.requests, "post", fake_post)
    monkeypatch.setattr(export_history.requests, "get", lambda url, timeout=0: DummyResponse(html))
    monkeypatch.setattr(export_history, "connect", lambda: (_ for _ in ()).throw(AssertionError("connect should not be called")))
    monkeypatch.setattr(export_history, "get_all_delegation_logs", lambda w3: (_ for _ in ()).throw(AssertionError("logs should not be called")))

    result = export_history.fetch_all_delegations("http://example.com", network="flare")

    assert result == [
        {
            "delegator": "a",
            "delegatee": "b",
            "amount": "1",
            "blockNumber": "2",
            "transactionHash": "h",
        }
    ]


def test_fallback_to_graphiql(monkeypatch):
    calls = []

    def fake_post(url, json=None, timeout=0):
        calls.append(url)
        if url.endswith("/graphql"):
            return DummyResponse("not found", status_code=404)
        return DummyResponse('{"data":{"delegationChangedEvents":[]}}', status_code=200)

    monkeypatch.setattr(export_history.requests, "post", fake_post)
    monkeypatch.setattr(export_history, "connect", lambda: (_ for _ in ()).throw(AssertionError("connect should not be called")))
    monkeypatch.setattr(export_history, "get_all_delegation_logs", lambda w3: (_ for _ in ()).throw(AssertionError("logs should not be called")))

    result = export_history.fetch_all_delegations("http://example.com/graphql", first=1)
    assert result == []
    assert calls == ["http://example.com/graphql", "http://example.com/graphiql"]


def test_scrape_failure_fallback_to_rpc(monkeypatch):
    def fake_post(url, json=None, timeout=0):
        return DummyResponse("bad html")

    def fake_get(url, timeout=0):
        raise export_history.requests.exceptions.HTTPError()

    rpc_called = {}

    def fake_connect():
        rpc_called["connect"] = True
        return "w3"

    def fake_logs(w3):
        rpc_called["logs"] = True
        return [{"log": 1}]

    monkeypatch.setattr(export_history.requests, "post", fake_post)
    monkeypatch.setattr(export_history.requests, "get", fake_get)
    monkeypatch.setattr(export_history, "connect", fake_connect)
    monkeypatch.setattr(export_history, "get_all_delegation_logs", fake_logs)

    result = export_history.fetch_all_delegations("http://example.com", network="flare")

    assert result == [{"log": 1}]
    assert rpc_called == {"connect": True, "logs": True}
