"""HTTP-Client und Parser für die PEGELONLINE-REST-API v2."""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import httpx

from . import __version__
from .models import CharacteristicValues, Measurement, Station

DEFAULT_BASE_URL = "https://www.pegelonline.wsv.de/webservices/rest-api/v2"
USER_AGENT = f"pegel-cli/{__version__} (+https://github.com/smlfg/pegel-cli)"
TIMEOUT = 10.0
CACHE_TTL = 300.0


class PegelError(Exception):
    """Fehler mit Exit-Code und genanntem nächsten Schritt."""

    exit_code = 1

    def __init__(self, message: str, next_step: str = ""):
        super().__init__(message)
        self.message = message
        self.next_step = next_step


class UsageError(PegelError):
    exit_code = 2


class NotFoundError(PegelError):
    exit_code = 1


class SourceError(PegelError):
    exit_code = 3


def base_url() -> str:
    raw = os.environ.get("PEGEL_BASE_URL", "").strip()
    value = raw or DEFAULT_BASE_URL
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise UsageError(
            f"PEGEL_BASE_URL ist keine gültige http(s)-URL: {value!r}",
            "PEGEL_BASE_URL korrigieren oder entfernen",
        )
    return value.rstrip("/")


def _cache_dir() -> Path:
    raw = os.environ.get("XDG_CACHE_HOME", "").strip()
    base = Path(raw) if raw else Path.home() / ".cache"
    path = base / "pegel-cli"
    try:
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(0o700)
    except OSError:
        return path
    return path


def _cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return _cache_dir() / f"{digest}.json"


def _read_cache(url: str) -> object | None:
    if os.environ.get("PEGEL_DISABLE_CACHE") == "1":
        return None
    path = _cache_path(url)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("url") != url:
        return None
    try:
        age = time.time() - float(data["ts"])
    except (KeyError, TypeError, ValueError):
        return None
    if age < 0 or age > CACHE_TTL:
        return None
    return data.get("payload")


def _write_cache(url: str, payload: object) -> None:
    if os.environ.get("PEGEL_DISABLE_CACHE") == "1":
        return
    path = _cache_path(url)
    data = {"url": url, "ts": time.time(), "payload": payload}
    try:
        path.write_text(json.dumps(data), encoding="utf-8")
        path.chmod(0o600)
    except OSError:
        return


def _build_url(path: str, params: list[tuple[str, str]] | None) -> str:
    url = base_url() + path
    if params:
        url += "?" + urlencode(params)
    return url


def get_json(path: str, params: list[tuple[str, str]] | None = None) -> object:
    url = _build_url(path, params)
    cached = _read_cache(url)
    if cached is not None:
        return cached
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        response = httpx.get(url, headers=headers, timeout=TIMEOUT, follow_redirects=True)
    except httpx.TimeoutException as exc:
        raise SourceError(
            "Zeitüberschreitung bei der Abfrage von PEGELONLINE",
            "Später erneut versuchen oder PEGEL_BASE_URL prüfen",
        ) from exc
    except httpx.RequestError as exc:
        raise SourceError(
            f"PEGELONLINE nicht erreichbar: {exc}",
            "Netzverbindung prüfen, später erneut versuchen oder PEGEL_BASE_URL prüfen",
        ) from exc
    if response.status_code != 200:
        raise SourceError(
            f"PEGELONLINE antwortet mit HTTP {response.status_code}",
            "Später erneut versuchen oder PEGEL_BASE_URL prüfen",
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise SourceError(
            "PEGELONLINE liefert kein gültiges JSON",
            "Später erneut versuchen; die API kann sich geändert haben",
        ) from exc
    _write_cache(url, payload)
    return payload


def _number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _state(value: object) -> str:
    if value in {"low", "normal", "high"}:
        return str(value)
    return "unknown"


def parse_current(data: object) -> Measurement | None:
    if not isinstance(data, dict):
        return None
    value = _number(data.get("value"))
    timestamp = data.get("timestamp")
    return Measurement(
        timestamp=str(timestamp) if timestamp else None,
        value=value,
        state_mnw_mhw=_state(data.get("stateMnwMhw")),
        state_nsw_hsw=_state(data.get("stateNswHsw")),
    )


def _w_timeseries(data: dict) -> dict | None:
    timeseries = data.get("timeseries")
    if not isinstance(timeseries, list):
        return None
    for entry in timeseries:
        if isinstance(entry, dict) and str(entry.get("shortname", "")).upper() == "W":
            return entry
    for entry in timeseries:
        if isinstance(entry, dict):
            return entry
    return None


def parse_stations(payload: object) -> list[Station]:
    if not isinstance(payload, list):
        raise SourceError(
            "Unerwartete Antwort der Pegelliste",
            "Später erneut versuchen; die API kann sich geändert haben",
        )
    stations: list[Station] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        water = entry.get("water") if isinstance(entry.get("water"), dict) else {}
        series = _w_timeseries(entry) or {}
        current = parse_current(series.get("currentMeasurement"))
        station = Station(
            uuid=str(entry.get("uuid", "")),
            name=str(entry.get("shortname") or entry.get("longname") or "?"),
            longname=str(entry.get("longname") or ""),
            km=_number(entry.get("km")),
            water_shortname=str(water.get("shortname") or ""),
            water_longname=str(water.get("longname") or ""),
            current=current,
            unit=str(series.get("unit") or "cm"),
        )
        stations.append(station)
    return stations


def parse_characteristics(payload: object) -> CharacteristicValues:
    if not isinstance(payload, dict):
        raise SourceError(
            "Unerwartete Antwort der Kennwerte",
            "Später erneut versuchen; die API kann sich geändert haben",
        )
    values: dict[str, float] = {}
    entries = payload.get("characteristicValues")
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            shortname = str(entry.get("shortname") or "").upper()
            value = _number(entry.get("value"))
            if shortname and value is not None:
                values[shortname] = value
    return CharacteristicValues(
        values=values,
        unit=str(payload.get("unit") or "cm"),
        current=parse_current(payload.get("currentMeasurement")),
    )


def parse_measurements(payload: object) -> list[Measurement]:
    if not isinstance(payload, list):
        raise SourceError(
            "Unerwartete Antwort der Messwerte",
            "Später erneut versuchen; die API kann sich geändert haben",
        )
    measurements: list[Measurement] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        value = _number(entry.get("value"))
        if value is None:
            continue
        measurements.append(
            Measurement(
                timestamp=str(entry.get("timestamp")) if entry.get("timestamp") else None,
                value=value,
            )
        )
    return measurements


def stations_by_fuzzy(term: str) -> list[Station]:
    payload = get_json(
        "/stations.json",
        [
            ("fuzzyId", term.lower()),
            ("includeTimeseries", "true"),
            ("includeCurrentMeasurement", "true"),
        ],
    )
    return parse_stations(payload)


def stations_by_water(shortname: str) -> list[Station]:
    payload = get_json(
        "/stations.json",
        [
            ("waters", shortname),
            ("includeTimeseries", "true"),
            ("includeCurrentMeasurement", "true"),
        ],
    )
    return parse_stations(payload)


def waters() -> list[dict[str, str]]:
    payload = get_json("/waters.json")
    if not isinstance(payload, list):
        raise SourceError(
            "Unerwartete Antwort der Gewässerliste",
            "Später erneut versuchen; die API kann sich geändert haben",
        )
    result: list[dict[str, str]] = []
    for entry in payload:
        if isinstance(entry, dict):
            result.append(
                {
                    "shortname": str(entry.get("shortname") or ""),
                    "longname": str(entry.get("longname") or ""),
                }
            )
    return result


def characteristic_values(uuid: str) -> CharacteristicValues:
    payload = get_json(
        f"/stations/{uuid}/W.json",
        [
            ("includeCurrentMeasurement", "true"),
            ("includeCharacteristicValues", "true"),
        ],
    )
    return parse_characteristics(payload)


def measurements(uuid: str, days: int) -> list[Measurement]:
    payload = get_json(
        f"/stations/{uuid}/W/measurements.json",
        [("start", f"P{days}D")],
    )
    return parse_measurements(payload)


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def trend_3h(current: Measurement | None, values: list[Measurement]) -> float | None:
    """Differenz zwischen aktuellem Wert und der Messung vor drei Stunden."""
    if current is None or current.value is None:
        return None
    now = parse_timestamp(current.timestamp)
    if now is None or not values:
        return None
    target = now - timedelta(hours=3)
    best: Measurement | None = None
    best_delta: float | None = None
    for entry in values:
        stamp = parse_timestamp(entry.timestamp)
        if stamp is None or entry.value is None:
            continue
        delta = abs((stamp - target).total_seconds())
        if best_delta is None or delta < best_delta:
            best = entry
            best_delta = delta
    if best is None or best.value is None:
        return None
    return float(round(current.value - best.value))
