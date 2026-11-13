"""Unit-Tests für Client und Parser gegen die UX-Fixtures."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from pegel import client
from pegel.models import format_km

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "ux"
SCRATCH = ROOT / "scratch" / "tmp"


def _fixture(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="pegel-unit-", dir=SCRATCH))
    monkeypatch.setenv("XDG_CACHE_HOME", str(work / "cache"))
    monkeypatch.setenv("PEGEL_DISABLE_CACHE", "1")
    monkeypatch.setenv("PEGEL_BASE_URL", "http://127.0.0.1:9")
    yield


def test_parse_heilbronn_station() -> None:
    stations = client.parse_stations(_fixture("stations_heilbronn.json"))
    assert len(stations) == 1
    station = stations[0]
    assert station.name == "Heilbronn Schleuse UP"
    assert station.water_shortname == "NECKAR"
    assert station.km == 113.3
    assert station.current is not None
    assert station.current.value == 221.0
    assert station.current.state_nsw_hsw == "normal"
    assert station.current.state_mnw_mhw == "unknown"
    assert station.benannt() == "Heilbronn Schleuse UP (NECKAR, km 113,3)"


def test_parse_mannheim_stations() -> None:
    stations = client.parse_stations(_fixture("stations_mannheim.json"))
    assert [station.name for station in stations] == ["MANNHEIM", "Mannheim Neckar"]
    assert [station.km for station in stations] == [424.733, 3.1]
    assert format_km(stations[0].km) == "424,7"


def test_parse_neckar_stations_order() -> None:
    stations = client.parse_stations(_fixture("stations_neckar.json"))
    assert len(stations) == 5
    assert [station.name for station in stations][0] == "Mannheim Neckar"
    assert stations[-1].name == "Heidelberg UP"


def test_parse_characteristics() -> None:
    values = client.parse_characteristics(_fixture("heidelberg_w.json"))
    assert values.unit == "cm"
    assert values.values["MNW"] == 207.0
    assert values.values["MW"] == 220.0
    assert values.values["MHW"] == 401.0
    assert values.values["HSW"] == 260.0
    assert "GlW" not in values.values
    assert values.current is not None
    assert values.current.value == 208.0


def test_parse_measurements_and_trend() -> None:
    current = client.parse_current(_fixture("stations_heilbronn.json")[0]["timeseries"][0]["currentMeasurement"])
    values = client.parse_measurements(_fixture("heilbronn_messungen_p1d.json"))
    assert len(values) == 95
    assert min(entry.value for entry in values if entry.value is not None) == 216.0
    assert max(entry.value for entry in values if entry.value is not None) == 228.0
    assert values[-1].value == 221.0
    assert client.trend_3h(current, values) == 0.0


def test_parse_waters() -> None:
    waters = _fixture("waters.json")
    assert any(entry["shortname"] == "NECKAR" for entry in waters)


def test_base_url_rejects_invalid(monkeypatch) -> None:
    monkeypatch.setenv("PEGEL_BASE_URL", "nicht-eine-url")
    with pytest.raises(client.UsageError):
        client.base_url()


def test_get_json_builds_url_and_follows_base(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class Response:
        status_code = 200

        def json(self):
            return [{"shortname": "NECKAR"}]

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs["headers"]
        return Response()

    monkeypatch.setattr(client.httpx, "get", fake_get)
    monkeypatch.setenv("PEGEL_BASE_URL", "http://127.0.0.1:1234/api")
    result = client.get_json("/stations.json", [("fuzzyId", "Köln"), ("includeTimeseries", "true")])
    assert result == [{"shortname": "NECKAR"}]
    assert captured["url"].startswith("http://127.0.0.1:1234/api/stations.json?")
    assert "fuzzyId=K%C3%B6ln" in captured["url"]
    assert "includeTimeseries=true" in captured["url"]
    assert "pegel-cli/0.1" in captured["headers"]["User-Agent"]


def test_get_json_http_error(monkeypatch) -> None:
    class Response:
        status_code = 503

        def json(self):
            return {}

    monkeypatch.setattr(client.httpx, "get", lambda *a, **k: Response())
    with pytest.raises(client.SourceError):
        client.get_json("/stations.json")


def test_get_json_invalid_json(monkeypatch) -> None:
    class Response:
        status_code = 200

        def json(self):
            raise ValueError("kaputt")

    monkeypatch.setattr(client.httpx, "get", lambda *a, **k: Response())
    with pytest.raises(client.SourceError):
        client.get_json("/stations.json")


def test_get_json_network_error(monkeypatch) -> None:
    def fake_get(*args, **kwargs):
        raise client.httpx.ConnectError("kein Netz")

    monkeypatch.setattr(client.httpx, "get", fake_get)
    with pytest.raises(client.SourceError):
        client.get_json("/stations.json")
