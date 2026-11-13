"""Unterkommando `pegel fluss NAME`."""

from __future__ import annotations

import difflib

from . import client
from .models import format_km
from .output import emit_json, format_value


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _score(name: str, water: dict[str, str]) -> float:
    normalized = _normalize(name)
    best = 0.0
    for candidate in (water.get("shortname", ""), water.get("longname", "")):
        score = difflib.SequenceMatcher(None, normalized, _normalize(candidate)).ratio()
        best = max(best, score)
    return best


def resolve_water(name: str, waters: list[dict[str, str]]) -> dict[str, str]:
    normalized = _normalize(name)
    exact = [
        water
        for water in waters
        if normalized
        in {_normalize(water.get("shortname", "")), _normalize(water.get("longname", ""))}
    ]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        names = ", ".join(water["shortname"] for water in exact)
        raise client.UsageError(
            f"Gewässername {name!r} ist mehrdeutig: {names}.",
            "Kürzel oder genaueren Gewässernamen angeben",
        )
    scored = [(_score(name, water), water) for water in waters]
    best = max((score for score, _ in scored), default=0.0)
    if best >= 0.6:
        candidates = [water for score, water in scored if score >= best - 1e-9]
        if len(candidates) == 1:
            return candidates[0]
        names = ", ".join(water["shortname"] for water in candidates)
        raise client.UsageError(
            f"Gewässername {name!r} passt zu mehreren Einträgen: {names}.",
            "Kürzel oder genaueren Gewässernamen angeben",
        )
    suggestions = difflib.get_close_matches(
        name.upper(),
        [water["shortname"] for water in waters],
        n=3,
        cutoff=0.3,
    )
    hint = f"Ähnliche Namen: {', '.join(suggestions)}" if suggestions else "Gewässerliste prüfen"
    raise client.NotFoundError(
        f"Gewässer {name!r} nicht gefunden.",
        f"{hint}; `pegel suche ORT` findet Pegel über Ortsnamen",
    )


def _pegel_dict(station) -> dict[str, object]:
    return {
        "name": station.name,
        "gewaesser": station.water_shortname,
        "km": station.km,
        "wasserstand_cm": station.current.value if station.current else None,
        "einheit": station.unit,
        "zeit": station.current.timestamp if station.current else None,
    }


def _nur_hoch(station) -> bool:
    current = station.current
    if current is None:
        return False
    return current.state_mnw_mhw == "high" or current.state_nsw_hsw == "high"


def run(args, json_mode: bool) -> int:
    water = resolve_water(args.name, client.waters())
    stations = client.stations_by_water(water["shortname"])
    stations.sort(key=lambda station: (station.km is None, station.km or 0.0))
    if args.nur_hoch:
        stations = [station for station in stations if _nur_hoch(station)]
    if json_mode:
        emit_json(
            {
                "befehl": "fluss",
                "gewaesser": water["shortname"],
                "anzahl": len(stations),
                "pegel": [_pegel_dict(station) for station in stations],
            }
        )
        return 0
    if not stations:
        if args.nur_hoch:
            print(f"{water['shortname']}: keine Pegel mit hohem Wasserstand.")
        else:
            print(f"{water['shortname']}: keine Pegel gefunden.")
        return 0
    print(f"{water['shortname']}: {len(stations)} Pegel")
    for index, station in enumerate(stations, start=1):
        value = format_value(station.current.value if station.current else None)
        print(
            f"{index}) {station.name} (km {format_km(station.km)}): "
            f"{value} {station.unit}"
        )
    return 0
