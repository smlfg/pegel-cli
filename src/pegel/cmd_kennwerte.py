"""Unterkommando `pegel kennwerte ORT`."""

from __future__ import annotations

from . import client
from .output import (
    emit_json,
    format_value,
    select_station,
    station_dict,
)

ORDER = ["MNW", "MW", "MHW", "HSW", "GlW"]


def run(args, json_mode: bool) -> int:
    stations = client.stations_by_fuzzy(args.ort)
    station = select_station(
        stations,
        args.ort,
        json_mode=json_mode,
        erster=getattr(args, "erster", False),
    )
    values = client.characteristic_values(station.uuid)
    current = values.current or station.current
    aktuell = current.value if current is not None else None
    kennwerte = {
        shortname: values.values[shortname]
        for shortname in ORDER
        if shortname in values.values
    }
    if json_mode:
        emit_json(
            {
                "befehl": "kennwerte",
                "pegel": station_dict(station),
                "kennwerte": kennwerte,
                "aktuell_cm": aktuell,
                "einheit": values.unit,
            }
        )
        return 0
    print(f"Kennwerte: {station.benannt()}")
    for shortname in ORDER:
        if shortname in kennwerte:
            print(f"{shortname}: {format_value(kennwerte[shortname])} {values.unit}")
    if aktuell is not None:
        print(f"Aktuell: {format_value(aktuell)} {values.unit}")
    return 0
