"""API clients: checked with saved sample responses, so no key or network is needed."""
import pandas as pd
import pytest

from fmo import eia, fred, http


class FakeResponse:
    def __init__(self, status, body=None, text=""):
        self.status_code, self._body, self.text = status, body, text

    def json(self):
        return self._body


def test_eia_rows_become_sorted_prices():
    rows = [
        {"period": "2026-08-31", "value": "5.599"},
        {"period": "2026-01-12", "value": "3.459"},
        {"period": "2026-01-12", "value": "3.459"},  # duplicate week
        {"period": "2026-02-02", "value": None},     # missing value
    ]
    df = eia.to_frame(rows)
    assert list(df.columns) == ["date", "price"]
    assert df["date"].is_monotonic_increasing
    assert df["price"].tolist() == [3.459, 5.599]


def test_eia_pages_until_total(monkeypatch):
    pages = [
        {"response": {"total": "3", "data": [{"period": "2026-01-05", "value": "3.5"},
                                             {"period": "2026-01-12", "value": "3.6"}]}},
        {"response": {"total": "3", "data": [{"period": "2026-01-19", "value": "3.7"}]}},
    ]
    offsets = []

    def fake_get(url, params):
        offsets.append(params["offset"])
        return pages[len(offsets) - 1]

    monkeypatch.setattr(eia, "get_json", fake_get)
    df = eia.fetch_diesel("test-key")
    assert offsets == [0, 2]
    assert len(df) == 3


def test_fred_missing_values_are_dropped():
    obs = [{"date": "2026-07-01", "value": "113.2"}, {"date": "2026-08-01", "value": "."}]
    df = fred.to_frame(obs)
    assert df["value"].tolist() == [113.2]
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_http_error_hides_api_key(monkeypatch):
    monkeypatch.setattr(http.requests, "get",
                        lambda *a, **k: FakeResponse(403, text="bad key SECRET123"))
    with pytest.raises(RuntimeError) as err:
        http.get_json("https://example.test", {"api_key": "SECRET123"})
    assert "SECRET123" not in str(err.value)
    assert "403" in str(err.value)


def test_http_retries_rate_limit(monkeypatch):
    responses = [FakeResponse(429), FakeResponse(200, {"ok": True})]
    monkeypatch.setattr(http.requests, "get", lambda *a, **k: responses.pop(0))
    monkeypatch.setattr(http.time, "sleep", lambda s: None)
    assert http.get_json("https://example.test", {}) == {"ok": True}
