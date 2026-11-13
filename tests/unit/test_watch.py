"""Tests für `pegel watch` und den lokalen Zustand."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path

import pytest

from pegel import client, state
from pegel.cli import build_parser
from pegel.cmd_watch import run as run_watch

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / "scratch" / "tmp"


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="pegel-watch-", dir=SCRATCH))
    monkeypatch.setenv("XDG_STATE_HOME", str(work / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(work / "cache"))
    yield work


def _station(monkeypatch, value: float = 221.0):
    station = client.parse_stations(
        json.loads(
            (ROOT / "tests" / "fixtures" / "ux" / "stations_heilbronn.json").read_text(
                encoding="utf-8"
            )
        )
    )[0]
    assert station.current is not None
    station.current.value = value
    monkeypatch.setattr(client, "stations_by_fuzzy", lambda term: [station])
    return station


def _args(*extra: str):
    return build_parser().parse_args(["watch", "Heilbronn", *extra])


def test_watch_erster_aufruf_und_zustand(monkeypatch, capsys, _isolated) -> None:
    _station(monkeypatch, 221.0)
    assert run_watch(_args(), False) == 0
    output = capsys.readouterr().out
    assert "Watch: Heilbronn Schleuse UP (NECKAR, km 113,3)" in output
    assert "Aktuell: 221 cm" in output
    assert "Seit letztem Aufruf: erster Aufruf" in output

    path = state.state_path()
    assert path.is_file()
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data[stations_uuid()]["wert"] == 221.0


def stations_uuid() -> str:
    return "f77df170-d23a-451c-9c43-b1580ccd3e2c"


def test_watch_aenderung_und_schwelle(monkeypatch, capsys, _isolated) -> None:
    _station(monkeypatch, 221.0)
    run_watch(_args("--ueber", "300"), False)
    capsys.readouterr()

    _station(monkeypatch, 242.0)
    assert run_watch(_args("--ueber", "300"), False) == 0
    output = capsys.readouterr().out
    assert "Seit letztem Aufruf: +21 cm" in output
    assert "Schwelle: über 300 cm" in output
    assert "Status: unter Schwelle" in output


def test_watch_unter_schwelle_ueberschritten(monkeypatch, capsys, _isolated) -> None:
    _station(monkeypatch, 198.0)
    assert run_watch(_args("--unter", "200"), False) == 0
    output = capsys.readouterr().out
    assert "Status: unter Schwelle" in output


def test_watch_json(monkeypatch, capsys, _isolated) -> None:
    _station(monkeypatch, 221.0)
    assert run_watch(_args("--ueber", "300", "--json"), True) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["befehl"] == "watch"
    assert payload["aktuell_cm"] == 221.0
    assert payload["erster_aufruf"] is True
    assert payload["schwelle"] == {"ueber": 300}
    assert payload["ueberschritten"] is False


def test_watch_ohne_schwelle(monkeypatch, capsys, _isolated) -> None:
    _station(monkeypatch, 221.0)
    assert run_watch(_args(), False) == 0
    output = capsys.readouterr().out
    assert "Schwelle:" not in output
    assert "Status:" not in output
