"""Unterkommando `pegel watch ORT [--ueber CM|--unter CM]`."""

from __future__ import annotations

from . import client, state
from .output import (
    emit_json,
    format_delta,
    format_value,
    select_station,
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
    data = state.load()
    previous = data.get(station.uuid)
    previous_value = None
    if isinstance(previous, dict):
        raw = previous.get("wert")
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            previous_value = float(raw)
    erster_aufruf = previous_value is None
    aenderung = None if previous_value is None else float(round(current.value - previous_value))

    schwelle: dict[str, int] | None = None
    if args.ueber is not None:
        schwelle = {"ueber": int(args.ueber)}
        ueberschritten = current.value >= args.ueber
    elif args.unter is not None:
        schwelle = {"unter": int(args.unter)}
        ueberschritten = current.value <= args.unter
    else:
        ueberschritten = None

    data[station.uuid] = {
        "name": station.name,
        "gewaesser": station.water_shortname,
        "wert": current.value,
        "zeit": current.timestamp,
        "schwelle": schwelle,
        "ueberschritten": ueberschritten,
    }
    try:
        state.save(data)
    except OSError as exc:
        raise client.PegelError(
            f"Watch-Zustand konnte nicht gespeichert werden: {exc}",
            "Schreibrechte für XDG_STATE_HOME prüfen",
        ) from exc

    if json_mode:
        emit_json(
            {
                "befehl": "watch",
                "pegel": station_dict(station),
                "aktuell_cm": current.value,
                "aenderung_cm": aenderung,
                "erster_aufruf": erster_aufruf,
                "schwelle": schwelle,
                "ueberschritten": ueberschritten,
            }
        )
        return 0

    print(f"Watch: {station.benannt()}")
    print(f"Aktuell: {format_value(current.value)} {station.unit}")
    if erster_aufruf:
        print("Seit letztem Aufruf: erster Aufruf")
    else:
        print(f"Seit letztem Aufruf: {format_delta(aenderung)} {station.unit}")
    if args.ueber is not None:
        print(f"Schwelle: über {args.ueber} {station.unit}")
        print("Status: über Schwelle" if ueberschritten else "Status: unter Schwelle")
    elif args.unter is not None:
        print(f"Schwelle: unter {args.unter} {station.unit}")
        print("Status: unter Schwelle" if ueberschritten else "Status: über Schwelle")
    return 0
