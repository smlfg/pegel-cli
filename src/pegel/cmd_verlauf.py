"""Unterkommando `pegel verlauf ORT [--tage N]`."""

from __future__ import annotations

from . import client
from .output import (
    emit_json,
    format_value,
    select_station,
    station_dict,
)


def run(args, json_mode: bool) -> int:
    days = args.tage
    if days < 1 or days > 30:
        raise client.UsageError(
            f"--tage muss zwischen 1 und 30 liegen (angegeben: {days}).",
            "Zum Beispiel `pegel verlauf ORT --tage 1` verwenden",
        )
    stations = client.stations_by_fuzzy(args.ort)
    station = select_station(
        stations,
        args.ort,
        json_mode=json_mode,
        erster=getattr(args, "erster", False),
    )
    values = client.measurements(station.uuid, days)
    if not values:
        raise client.NotFoundError(
            f"Für {station.name} liegen keine Messwerte vor.",
            "Später erneut versuchen oder einen anderen Pegel wählen",
        )
    numbers = [entry.value for entry in values if entry.value is not None]
    minimum = min(numbers)
    maximum = max(numbers)
    aktuell = values[-1].value
    if json_mode:
        emit_json(
            {
                "befehl": "verlauf",
                "pegel": station_dict(station),
                "tage": days,
                "min_cm": minimum,
                "max_cm": maximum,
                "aktuell_cm": aktuell,
                "einheit": station.unit,
                "punkte": len(values),
                "werte": [
                    {
                        "zeit": entry.timestamp,
                        "wasserstand_cm": entry.value,
                    }
                    for entry in values
                ],
            }
        )
        return 0
    print(f"Verlauf: {station.name} ({station.water_shortname}), letzte {days * 24} h")
    print(f"Minimum: {format_value(minimum)} {station.unit}")
    print(f"Maximum: {format_value(maximum)} {station.unit}")
    print(f"Aktuell: {format_value(aktuell)} {station.unit}")
    print(f"Punkte: {len(values)}")
    return 0
