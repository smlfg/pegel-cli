"""Unterkommando `pegel suche ORT`."""

from __future__ import annotations

from . import client
from .output import emit_json, list_line


def run(args, json_mode: bool) -> int:
    stations = client.stations_by_fuzzy(args.ort)
    if json_mode:
        emit_json(
            {
                "befehl": "suche",
                "treffer": [
                    {
                        "name": station.name,
                        "gewaesser": station.water_shortname,
                        "km": station.km,
                        "wasserstand_cm": (
                            station.current.value if station.current else None
                        ),
                        "einheit": station.unit,
                        "zeit": station.current.timestamp if station.current else None,
                    }
                    for station in stations
                ],
            }
        )
        return 0
    if not stations:
        print(f"Keine Pegel zu {args.ort!r} gefunden.")
        print("Nächster Schritt: Anderen Ortsnamen versuchen oder `pegel fluss NAME` nutzen.")
        return 0
    for index, station in enumerate(stations, start=1):
        print(list_line(index, station))
    return 0
