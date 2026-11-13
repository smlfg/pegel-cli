"""Akzeptanztests aus den UX-Sitzungen gegen den Fake-Server.

Jede Sitzung aus ``docs/UX.md`` hat hier mindestens einen Test. Die Tests
starten das Tool als Subprozess (``python -m pegel``) und setzen
``PEGEL_BASE_URL`` auf den lokalen Fake-Server. Die Netzwerk-Sandbox aus
``tests/harness/sitecustomize.py`` blockiert alle anderen Ziele.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tests" / "harness"
UX_SPEC = ROOT / "docs" / "UX.md"
SCRATCH_TMP = ROOT / "scratch" / "tmp"

if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

from fake_server import FakeServer  # noqa: E402
from ux_session import PtySession, strip_ansi  # noqa: E402
from ux_spec import parse  # noqa: E402


def _workdir() -> Path:
    SCRATCH_TMP.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="pegel-acceptance-", dir=SCRATCH_TMP))


def _command(*args: str) -> list[str]:
    return [sys.executable, "-m", "pegel", *args]


def _environment(server: FakeServer) -> tuple[dict[str, str], Path]:
    home = _workdir() / "home"
    for relative in (".cache", ".local/state", ".config"):
        (home / relative).mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(
        {
            "HOME": str(home),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "XDG_STATE_HOME": str(home / ".local" / "state"),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "PEGEL_BASE_URL": server.base_url,
            "PEGEL_HEUTE": "2026-11-13",
            "PYTHONPATH": str(HARNESS),
            "PYTHONUNBUFFERED": "1",
            "TERM": "xterm-256color",
            "NO_COLOR": "1",
            "LANG": "C.UTF-8",
            "ACCEPTANCE_SANDBOX": "1",
            "ACCEPTANCE_NET_LOG": str(home / "net.log"),
            "UX_REPO_DIR": str(ROOT),
        }
    )
    return env, home


def _run_tty(server: FakeServer, *args: str, timeout: float = 30.0) -> tuple[int | None, str]:
    env, _ = _environment(server)
    session = PtySession(_command(*args), env=env, cwd=ROOT)
    try:
        code = session.wait_exit(timeout)
        output = strip_ansi(session.transcript)
    finally:
        session.close()
    return code, output


def _run_pipe(server: FakeServer, *args: str) -> subprocess.CompletedProcess[str]:
    env, _ = _environment(server)
    return subprocess.run(
        _command(*args),
        cwd=ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
    )


@pytest.fixture()
def server() -> FakeServer:
    spec = parse(UX_SPEC)
    assert spec.errors == []
    with FakeServer(spec, ROOT) as running:
        yield running


def test_stand_heilbronn(server: FakeServer) -> None:
    code, output = _run_tty(server, "stand", "Heilbronn")

    assert code == 0, output
    assert "Pegel: Heilbronn Schleuse UP (NECKAR, km 113,3)" in output
    assert "Wasserstand: 221 cm" in output
    assert "Stand: 13.11.2026 09:15" in output
    assert "Einordnung: normal (NSW/HSW), MNW/MHW unbekannt" in output
    assert "Trend (3 h): 0 cm" in output
    assert server.requests


def test_suche_mannheim(server: FakeServer) -> None:
    code, output = _run_tty(server, "suche", "Mannheim")

    assert code == 0, output
    assert "1) MANNHEIM (RHEIN, km 424,7): 145 cm" in output
    assert "2) Mannheim Neckar (NECKAR, km 3,1): 146 cm" in output
    assert server.requests


def test_fluss_neckar(server: FakeServer) -> None:
    code, output = _run_tty(server, "fluss", "Neckar")

    assert code == 0, output
    assert "NECKAR: 5 Pegel" in output
    assert "1) Mannheim Neckar (km 3,1): 146 cm" in output
    assert "2) Feudenheim Schleuse UP (km 6,1): 133 cm" in output
    assert "3) Ladenburg Wehr UP (km 11,9): 685 cm" in output
    assert "4) Schwabenheim Schleuse UP (km 17,6): 214 cm" in output
    assert "5) Heidelberg UP (km 26,1): 208 cm" in output
    assert server.requests


def test_verlauf_heilbronn(server: FakeServer) -> None:
    code, output = _run_tty(server, "verlauf", "Heilbronn", "--tage", "1")

    assert code == 0, output
    assert "Verlauf: Heilbronn Schleuse UP (NECKAR), letzte 24 h" in output
    assert "Minimum: 216 cm" in output
    assert "Maximum: 228 cm" in output
    assert "Aktuell: 221 cm" in output
    assert "Punkte: 95" in output
    assert server.requests


def test_kennwerte_heidelberg(server: FakeServer) -> None:
    code, output = _run_tty(server, "kennwerte", "Heidelberg")

    assert code == 0, output
    assert "Kennwerte: Heidelberg UP (NECKAR, km 26,1)" in output
    assert "MNW: 207 cm" in output
    assert "MW: 220 cm" in output
    assert "MHW: 401 cm" in output
    assert "HSW: 260 cm" in output
    assert "Aktuell: 208 cm" in output
    assert server.requests


def test_stand_json_bei_pipe(server: FakeServer) -> None:
    result = _run_pipe(server, "stand", "Heilbronn", "--json")

    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["befehl"] == "stand"
    assert data["pegel"]["name"] == "Heilbronn Schleuse UP"
    assert data["pegel"]["gewaesser"] == "NECKAR"
    assert data["wasserstand_cm"] == 221.0
    assert data["trend_3h_cm"] == 0
    assert data["einordnung"] == {"nsw_hsw": "normal", "mnw_mhw": "unknown"}
    assert server.requests
