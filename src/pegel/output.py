"""Gemeinsame Text- und JSON-Ausgabe."""

from __future__ import annotations

import json
import sys
from datetime import datetime

from . import client
from .models import Measurement, Station, format_km

STATE_TEXT = {
    "low": "niedrig",
    "normal": "normal",
    "high": "hoch",
    "unknown": "unbekannt",
}


class AmbiguousStations(client.UsageError):
    """Mehrere Pegel, aber keine interaktive Auswahl möglich."""

    def __init__(self, message: str, next_step: str, stations: list[Station]):
        super().__init__(message, next_step)
        self.stations = stations


def state_text(value: str) -> str:
    return STATE_TEXT.get(value, "unbekannt")


def format_timestamp(value: str | None) -> str:
    if not value:
        return "unbekannt"
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        return value
    return stamp.strftime("%d.%m.%Y %H:%M")


def format_value(value: float | None) -> str:
    if value is None:
        return "unbekannt"
    return f"{value:.0f}"


def format_delta(value: float | None) -> str:
    if value is None:
        return "unbekannt"
    number = int(round(value))
    if number == 0:
        return "0"
    return f"{number:+d}"


def station_dict(station: Station) -> dict[str, object]:
    return {
        "name": station.name,
        "gewaesser": station.water_shortname,
        "km": station.km,
    }


def measurement_dict(measurement: Measurement | None, unit: str = "cm") -> dict[str, object]:
    if measurement is None:
        return {"wasserstand_cm": None, "einheit": unit, "zeit": None}
    return {
        "wasserstand_cm": measurement.value,
        "einheit": unit,
        "zeit": measurement.timestamp,
    }


def list_line(index: int, station: Station) -> str:
    value = format_value(station.current.value if station.current else None)
    return (
        f"{index}) {station.name} ({station.water_shortname}, "
        f"km {format_km(station.km)}): {value} {station.unit}"
    )


def emit_json(payload: object) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def select_station(
    stations: list[Station],
    term: str,
    *,
    json_mode: bool,
    erster: bool,
) -> Station:
    if not stations:
        raise client.NotFoundError(
            f"Kein Pegel zu {term!r} gefunden.",
            "Anderen Ortsnamen versuchen oder `pegel suche ORT` nutzen",
        )
    if len(stations) == 1:
        return stations[0]
    if erster:
        return stations[0]
    if json_mode or not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise AmbiguousStations(
            f"Mehrere Pegel passen zu {term!r}.",
            "Genaueren Suchbegriff verwenden oder `--erster` setzen",
            stations,
        )
    for index, station in enumerate(stations, start=1):
        print(list_line(index, station), file=sys.stderr)
    sys.stderr.write(f"Auswahl [1-{len(stations)}]: ")
    sys.stderr.flush()
    try:
        answer = sys.stdin.readline()
    except EOFError:
        raise client.UsageError(
            "Keine Auswahl getroffen.",
            "Erneut starten und eine Nummer eingeben oder `--erster` verwenden",
        )
    if not answer:
        raise client.UsageError(
            "Keine Auswahl getroffen.",
            "Erneut starten und eine Nummer eingeben oder `--erster` verwenden",
        )
    answer = answer.strip()
    try:
        index = int(answer)
    except ValueError:
        raise client.UsageError(
            f"Ungültige Auswahl: {answer!r}",
            "Eine Zahl aus der Liste eingeben oder `--erster` verwenden",
        )
    if not 1 <= index <= len(stations):
        raise client.UsageError(
            f"Auswahl außerhalb von 1 bis {len(stations)}: {index}",
            "Eine Zahl aus der Liste eingeben oder `--erster` verwenden",
        )
    return stations[index - 1]
