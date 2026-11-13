"""Fehlervertrag, Auswahl und Namensauflösung."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from pegel import client
from pegel.cmd_fluss import resolve_water
from pegel.output import AmbiguousStations, select_station

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "ux"
SCRATCH = ROOT / "scratch" / "tmp"


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="pegel-cli-", dir=SCRATCH))
    monkeypatch.setenv("XDG_CACHE_HOME", str(work / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(work / "state"))
    monkeypatch.setenv("PEGEL_DISABLE_CACHE", "1")
    monkeypatch.setenv("PEGEL_BASE_URL", "http://127.0.0.1:9")
    yield


def _stations(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _waters():
    return json.loads((FIXTURES / "waters.json").read_text(encoding="utf-8"))


def test_resolve_water_exact_and_typo() -> None:
    waters = _waters()
    assert resolve_water("neckar", waters)["shortname"] == "NECKAR"
    assert resolve_water("Nekar", waters)["shortname"] == "NECKAR"
    assert resolve_water("Rhein", waters)["shortname"] == "RHEIN"


def test_resolve_water_unknown() -> None:
    with pytest.raises(client.NotFoundError) as excinfo:
        resolve_water("Xyzfluss", _waters())
    assert excinfo.value.exit_code == 1
    assert excinfo.value.next_step


def test_select_station_no_hit() -> None:
    with pytest.raises(client.NotFoundError) as excinfo:
        select_station([], "Nirgendwo", json_mode=False, erster=False)
    assert excinfo.value.exit_code == 1


def test_select_station_ambiguous_without_tty(monkeypatch) -> None:
    stations = client.parse_stations(_stations("stations_mannheim.json"))
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    with pytest.raises(AmbiguousStations) as excinfo:
        select_station(stations, "Mannheim", json_mode=False, erster=False)
    assert excinfo.value.exit_code == 2
    assert len(excinfo.value.stations) == 2


def test_select_station_erster() -> None:
    stations = client.parse_stations(_stations("stations_mannheim.json"))
    chosen = select_station(stations, "Mannheim", json_mode=True, erster=True)
    assert chosen.name == "MANNHEIM"


def test_main_ambiguous_json(monkeypatch, capsys) -> None:
    from pegel.cli import main

    stations = client.parse_stations(_stations("stations_mannheim.json"))
    monkeypatch.setattr(client, "stations_by_fuzzy", lambda term: stations)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    code = main(["stand", "Mannheim", "--json"])
    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["fehler"].startswith("Mehrere Pegel")
    assert len(payload["treffer"]) == 2


def test_main_version_and_help(capsys) -> None:
    from pegel.cli import main

    assert main(["--version"]) == 0
    assert "pegel 0.1.0" in capsys.readouterr().out
    assert main(["--help"]) == 0
    out = capsys.readouterr().out
    for sub in ("suche", "stand", "verlauf", "fluss", "kennwerte", "watch"):
        assert sub in out


def test_main_usage_json(monkeypatch, capsys) -> None:
    from pegel.cli import main

    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    assert main(["unbekannt", "--json"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert "fehler" in payload
    assert "naechster_schritt" in payload


def test_main_network_error_json(monkeypatch, capsys) -> None:
    from pegel.cli import main

    def boom(path, params=None):
        raise client.SourceError("PEGELONLINE nicht erreichbar", "Später erneut versuchen")

    monkeypatch.setattr(client, "get_json", boom)
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    assert main(["suche", "Heilbronn"]) == 3
    payload = json.loads(capsys.readouterr().out)
    assert payload["fehler"] == "PEGELONLINE nicht erreichbar"


def test_main_keyboard_interrupt_without_traceback(monkeypatch, capsys) -> None:
    from pegel.cli import main

    def interrupt(path, params=None):
        raise KeyboardInterrupt

    monkeypatch.setattr(client, "get_json", interrupt)
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    assert main(["suche", "Heilbronn"]) == 130
    captured = capsys.readouterr()
    assert "Traceback" not in captured.out + captured.err
    payload = json.loads(captured.out)
    assert payload["fehler"] == "Abgebrochen."


def test_select_station_eof(monkeypatch) -> None:
    import io
    import sys

    stations = client.parse_stations(_stations("stations_mannheim.json"))
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    with pytest.raises(client.UsageError) as excinfo:
        select_station(stations, "Mannheim", json_mode=False, erster=False)
    assert excinfo.value.exit_code == 2


def test_select_station_invalid_choice(monkeypatch) -> None:
    import io
    import sys

    stations = client.parse_stations(_stations("stations_mannheim.json"))
    monkeypatch.setattr(sys, "stdin", io.StringIO("x\n"))
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    with pytest.raises(client.UsageError) as excinfo:
        select_station(stations, "Mannheim", json_mode=False, erster=False)
    assert excinfo.value.exit_code == 2
