"""Unterkommando `pegel stand ORT`."""

from __future__ import annotations

from . import client
from .output import (
    emit_json,
    format_delta,
    format_timestamp,
    format_value,
    select_station,
    state_text,
    station_dict,
)


def run(args, json_mode: bool) -> int:
    stations = client.stations_by_fuzzy(args.ort)
    station = select_station(
        stations,
        args.ort,
        json_mode=json_mode,
        erster=getattr(args, "erster", False),
    )
    current = station.current
    if current is None or current.value is None:
        raise client.SourceError(
            f"Für {station.name} liegt keine aktuelle Messung vor.",
            "Später erneut versuchen oder einen anderen Pegel wählen",
        )
    values = client.measurements(station.uuid, 1)
    trend = client.trend_3h(current, values)
    if json_mode:
        emit_json(
            {
                "befehl": "stand",
                "pegel": station_dict(station),
                "wasserstand_cm": current.value,
                "einheit": station.unit,
                "zeit": current.timestamp,
                "einordnung": {
                    "nsw_hsw": current.state_nsw_hsw,
                    "mnw_mhw": current.state_mnw_mhw,
                },
                "trend_3h_cm": trend,
            }
        )
        return 0
    print(f"Pegel: {station.benannt()}")
    print(f"Wasserstand: {format_value(current.value)} {station.unit}")
    print(f"Stand: {format_timestamp(current.timestamp)}")
    print(
        "Einordnung: "
        f"{state_text(current.state_nsw_hsw)} (NSW/HSW), "
        f"MNW/MHW {state_text(current.state_mnw_mhw)}"
    )
    print(f"Trend (3 h): {format_delta(trend)} {station.unit}")
    return 0
