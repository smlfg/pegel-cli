"""Kommandozeile für `pegel`."""

from __future__ import annotations

import argparse
import sys

from . import __version__, client
from .cmd_stand import run as run_stand
from .cmd_suche import run as run_suche
from .output import AmbiguousStations, emit_json


def _add_json(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Genau ein JSON-Objekt auf stdout ausgeben",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pegel",
        description=(
            "Live-Wasserstände der Bundeswasserstraßen über PEGELONLINE "
            "(inoffiziell, nur lesend)."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pegel {__version__}",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Genau ein JSON-Objekt auf stdout ausgeben",
    )
    subparsers = parser.add_subparsers(dest="befehl", metavar="BEFEHL", required=True)

    suche = subparsers.add_parser(
        "suche",
        help="Pegel nach Orts- oder Suchbegriff finden",
        description="Sucht Pegel case-insensitiv über die PEGELONLINE-Suche.",
    )
    suche.add_argument("ort", metavar="ORT", help="Orts- oder Suchbegriff")
    _add_json(suche)
    suche.set_defaults(func=run_suche)

    stand = subparsers.add_parser(
        "stand",
        help="Aktuellen Wasserstand mit Einordnung und Trend zeigen",
        description=(
            "Zeigt den aktuellen Wasserstand, die Einordnung nach MNW/MHW "
            "und NSW/HSW sowie den Trend der letzten drei Stunden."
        ),
    )
    stand.add_argument("ort", metavar="ORT", help="Orts- oder Suchbegriff")
    stand.add_argument(
        "--erster",
        action="store_true",
        help="Bei mehreren Treffern ohne Terminal den ersten Pegel verwenden",
    )
    _add_json(stand)
    stand.set_defaults(func=run_stand)

    return parser


def _json_requested(argv: list[str]) -> bool:
    return "--json" in argv or not sys.stdout.isatty()


def _print_error(exc: client.PegelError, json_mode: bool) -> int:
    if json_mode:
        payload: dict[str, object] = {
            "fehler": exc.message,
            "naechster_schritt": exc.next_step,
        }
        if isinstance(exc, AmbiguousStations):
            payload["treffer"] = [
                {
                    "name": station.name,
                    "gewaesser": station.water_shortname,
                    "km": station.km,
                    "wasserstand_cm": (
                        station.current.value if station.current else None
                    ),
                }
                for station in exc.stations
            ]
        emit_json(payload)
    else:
        print(f"Fehler: {exc.message}", file=sys.stderr)
        if exc.next_step:
            print(f"Nächster Schritt: {exc.next_step}", file=sys.stderr)
    return exc.exit_code


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    try:
        args = parser.parse_args(arguments)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        if code != 0 and _json_requested(arguments):
            emit_json(
                {
                    "fehler": "Ungültige Eingabe.",
                    "naechster_schritt": "`pegel --help` zeigt alle Befehle",
                }
            )
        return code

    json_mode = bool(getattr(args, "json", False)) or not sys.stdout.isatty()
    try:
        return int(args.func(args, json_mode) or 0)
    except AmbiguousStations as exc:
        return _print_error(exc, json_mode)
    except client.PegelError as exc:
        return _print_error(exc, json_mode)
    except KeyboardInterrupt:
        if json_mode:
            emit_json(
                {
                    "fehler": "Abgebrochen.",
                    "naechster_schritt": "Befehl erneut starten",
                }
            )
        else:
            print("Abgebrochen.", file=sys.stderr)
            print("Nächster Schritt: Befehl erneut starten.", file=sys.stderr)
        return 130
    except EOFError:
        return _print_error(
            client.UsageError(
                "Eingabe abgebrochen.",
                "Befehl erneut starten oder `--erster` verwenden",
            ),
            json_mode,
        )
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
