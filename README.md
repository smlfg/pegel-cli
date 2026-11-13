# pegel

Live-Wasserstände der Bundeswasserstraßen im Terminal: Pegel per Ortsname
finden, aktuellen Stand mit Einordnung und Trend sehen, Verlauf und Kennwerte
abrufen sowie alle Pegel eines Flusses auflisten. Quelle ist die offene
PEGELONLINE-REST-API der WSV (Datenlizenz DL-DE/Zero), ohne Login.

## Schnellstart

```bash
pipx install git+https://github.com/smlfg/pegel-cli
pegel stand Heilbronn
pegel suche Mannheim
pegel fluss Neckar
pegel verlauf Heilbronn --tage 1
pegel kennwerte Heidelberg
```

`pegel stand` wählt bei einem eindeutigen Ortsnamen direkt den Pegel und zeigt
Wasserstand, Messzeitpunkt, Einordnung (niedrig/normal/hoch) und den Trend der
letzten drei Stunden. `pegel suche` listet mehrere Treffer mit Fluss,
Kilometer und aktuellem Wert. `pegel fluss` löst den Gewässernamen auf und
sortiert die Pegel flussabwärts.

## Befehle

| Befehl | Aufgabe |
|---|---|
| `pegel suche ORT` | Pegel nach Orts- oder Suchbegriff finden |
| `pegel stand ORT` | Aktuellen Wasserstand mit Einordnung und 3-h-Trend zeigen |
| `pegel verlauf ORT [--tage N]` | Minimum, Maximum und aktuellen Wert der letzten Tage |
| `pegel fluss NAME [--nur-hoch]` | Alle Pegel eines Gewässers, flussabwärts sortiert |
| `pegel kennwerte ORT` | MNW, MW, MHW, HSW, GlW und aktueller Wert |
| `pegel watch ORT [--ueber CM\|--unter CM]` | Änderung seit dem letzten Aufruf und Schwelle |

Beispiele:

```bash
pegel suche Mannheim
pegel stand Heilbronn
pegel verlauf Heilbronn --tage 1
pegel fluss Neckar
pegel kennwerte Heidelberg
pegel watch Heilbronn --ueber 300
```

Bei mehreren Treffern fragt `pegel stand` im Terminal nach einer Nummer. Für
Agenten gibt es `--erster`; ohne Terminal und ohne `--erster` endet der Befehl
mit Exit 2 und einer Trefferliste. `--json` liefert genau ein JSON-Objekt;
ohne TTY geschieht das automatisch.

## Konfiguration

| Variable | Bedeutung |
|---|---|
| `PEGEL_BASE_URL` | Basis-URL der API, Standard `https://www.pegelonline.wsv.de/webservices/rest-api/v2`; für Fake-Server in Tests |
| `PEGEL_HEUTE` | Testdatum `JJJJ-MM-TT` für deterministische Watch-Ausgaben |
| `XDG_CACHE_HOME` | Cache-Basis, Standard `~/.cache`; Cache in `~/.cache/pegel-cli` (5 Minuten) |
| `XDG_STATE_HOME` | Zustandsbasis, Standard `~/.local/state`; Watch-Zustand in `~/.local/state/pegel-cli/watch.json` (0600) |

Es gibt keinen Login und keine Zugangsdaten. Das Tool sendet nur lesende
GET-Requests und speichert nichts außer Cache und lokalem Watch-Zustand.

## Exit-Codes

| Code | Bedeutung |
|---|---|
| `0` | Erfolg (auch bei leerer Suche oder Watch-Schwelle) |
| `1` | Kein Treffer oder sonstiger Fehler |
| `2` | Usage: ungültige Argumente, mehrdeutiger Treffer ohne Auswahl |
| `3` | Netzwerk- oder Quellfehler |
| `4` | Login nötig; bei `pegel` nicht verwendet |
| `130` | Abbruch mit Strg+C, ohne Traceback |

## Hinweis

`pegel` ist ein inoffizielles Werkzeug und steht in keiner Verbindung zur
Wasserstraßen- und Schifffahrtsverwaltung des Bundes. Die API kann sich ändern
oder ausfallen. Fehlende Werte werden als „unbekannt“ angezeigt, nicht
geschätzt.

## Daten und Lizenz

Die Wasserstandsdaten stammen von PEGELONLINE (WSV) und stehen unter
DL-DE/Zero. Der Code steht unter der MIT-Lizenz, Copyright smlfg. Details zur
Schnittstelle stehen in `INTERFACE.md`, Anforderungen und Nachfrage in
`ANFORDERUNGEN.md`.
