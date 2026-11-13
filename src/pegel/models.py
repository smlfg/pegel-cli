"""Datenmodelle der PEGELONLINE-Antworten."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Measurement:
    timestamp: str | None
    value: float | None
    state_mnw_mhw: str = "unknown"
    state_nsw_hsw: str = "unknown"
    unit: str = "cm"


@dataclass
class Station:
    uuid: str
    name: str
    longname: str
    km: float | None
    water_shortname: str
    water_longname: str
    current: Measurement | None = None
    unit: str = "cm"

    def benannt(self) -> str:
        """Name mit Gewässer und Kilometer für die Textausgabe."""
        teile = [self.name]
        if self.water_shortname:
            teile.append(f"({self.water_shortname}, km {format_km(self.km)})")
        return " ".join(teile)


def format_km(km: float | None) -> str:
    if km is None:
        return "?"
    return f"{km:.1f}".replace(".", ",")


@dataclass
class CharacteristicValues:
    values: dict[str, float] = field(default_factory=dict)
    unit: str = "cm"
    current: Measurement | None = None
