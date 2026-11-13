# Schnittstelle: pegel

Version: `0.1.0` (Konsolenskript `pegel`, Python-Paket `pegel`).

`pegel` liest ausschließlich öffentliche Wasserstandsdaten der PEGELONLINE-
REST-API. Alle Web-Aktionen sind `GET`; es gibt keinen Login und keine
schreibende Aktion.

## Aufruf

```text
pegel [--json] <unterkommando> [argumente] [optionen]
pegel --version
pegel --help
```

Globale Optionen:

| Option | Bedeutung |
|---|---|
| `--json` | Genau ein JSON-Objekt auf stdout. Prompts und Hinweise gehen auf stderr. |
| `--version` | Gibt `pegel 0.1.0` aus, Exit 0. |
| `-h`, `--help` | Hilfe zum Hauptbefehl bzw. Unterkommando, Exit 0. |

Ohne `--json` gilt: Ist stdout ein Terminal (TTY), wird lesbarer Text
ausgegeben. Ist stdout kein Terminal (Pipe, Datei, Agent), wird automatisch
JSON ausgegeben. Der Inhalt ist in beiden Fällen derselbe.

Positionale Argumente sind Orts-, Such- oder Flussnamen. IDs und Pflicht-
Optionen sind für die Kernaufgaben nicht nötig.

## Unterkommandos

### `pegel suche ORT`

Sucht Pegel case-insensitiv über `fuzzyId`. Umlaute werden URL-kodiert
unterstützt (`Köln`, `KÖLN`). Ein Suchbegriff darf mehrere Treffer liefern.

Ausgabe (Text), nummeriert in der Reihenfolge der API:

```text
1) MANNHEIM (RHEIN, km 424,7): 145 cm
2) Mannheim Neckar (NECKAR, km 3,1): 146 cm
```

Bei null Treffern: Meldung mit nächstem Schritt (anderer Ortsname,
`pegel fluss NAME`) und Exit 0. Die Suche selbst war erfolgreich.

Optionen: keine eigenen; `--json` global.

### `pegel stand ORT`

Zeigt den aktuellen Wasserstand eines Pegels mit Einordnung und Trend der
letzten drei Stunden. Der Trend ist die Differenz zwischen dem aktuellen Wert
und der Messung, die dem Zeitpunkt vor drei Stunden am nächsten liegt,
gerundet auf ganze Zentimeter. Format: `0 cm` bei null, sonst `+5 cm` bzw.
`-3 cm`.

Textausgabe bei genau einem Treffer:

```text
Pegel: Heilbronn Schleuse UP (NECKAR, km 113,3)
Wasserstand: 221 cm
Stand: 13.11.2026 09:15
Einordnung: normal (NSW/HSW), MNW/MHW unbekannt
Trend (3 h): 0 cm
```

Einordnungswerte der API werden so übersetzt: `low` → `niedrig`,
`normal` → `normal`, `high` → `hoch`, `unknown` → `unbekannt`.

Bei mehreren Treffern:

- TTY: nummerierte Liste, dann Prompt `Auswahl [1-N]: ` auf stderr. Eine
  gültige Nummer wählt den Pegel; ungültige Eingabe oder EOF endet ohne
  Traceback mit Exit 2.
- Kein TTY und `--erster` gesetzt: der erste Treffer wird verwendet.
- Kein TTY und kein `--erster`: Liste der Treffer und Exit 2. Der nächste
  Schritt ist `--erster` oder ein genauerer Suchbegriff.

Optionen:

| Option | Bedeutung |
|---|---|
| `--erster` | Bei mehreren Treffern ohne TTY den ersten verwenden. |

Kein Treffer: Exit 1 mit Vorschlag, den Ortsnamen zu prüfen oder
`pegel suche ORT` zu nutzen.

### `pegel verlauf ORT [--tage N]`

Ruft die Messwerte der letzten `N` Tage ab und zeigt Minimum, Maximum,
aktuellen Wert und Anzahl der Punkte. Standard `N=1`; erlaubt sind `1` bis
`30`. Die API liefert ein 15-Minuten-Raster.

Textausgabe:

```text
Verlauf: Heilbronn Schleuse UP (NECKAR), letzte 24 h
Minimum: 216 cm
Maximum: 228 cm
Aktuell: 221 cm
Punkte: 95
```

`letzte 24 h` entspricht `N * 24 h`. Bei mehreren Treffern gelten dieselben
Regeln wie bei `stand` (`--erster`, TTY-Auswahl, Exit 2).

Optionen:

| Option | Bedeutung |
|---|---|
| `--tage N` | Zeitraum in Tagen, `1` bis `30`, Standard `1`. Unparsebare oder außerhalb liegende Werte: Exit 2. |
| `--erster` | Bei mehreren Treffern ohne TTY den ersten verwenden. |

### `pegel fluss NAME`

Löst `NAME` über `/waters.json` gegen Kurz- und Langnamen auf. Groß-/
Kleinschreibung und Umlaute werden normalisiert. Ist kein exakter Treffer
vorhanden, wird eine eindeutige, ausreichend ähnliche Schreibweise akzeptiert
(Tippfehler-tolerant). Mehrere gleich gute Kandidaten: Liste und Exit 2.

Danach werden alle Pegel des Gewässers geladen und nach Kilometer aufsteigend
(flussabwärts) ausgegeben:

```text
NECKAR: 5 Pegel
1) Mannheim Neckar (km 3,1): 146 cm
2) Feudenheim Schleuse UP (km 6,1): 133 cm
3) Ladenburg Wehr UP (km 11,9): 685 cm
4) Schwabenheim Schleuse UP (km 17,6): 214 cm
5) Heidelberg UP (km 26,1): 208 cm
```

Optionen:

| Option | Bedeutung |
|---|---|
| `--nur-hoch` | Nur Pegel mit `stateMnwMhw=high` oder `stateNswHsw=high`. Ohne Treffer: Meldung und Exit 0. |

Unbekanntes Gewässer: Exit 1 mit Vorschlag aus der Gewässerliste.

### `pegel kennwerte ORT`

Zeigt die Kennwerte MNW, MW, MHW, HSW und – falls vorhanden – GlW mit Einheit
sowie den aktuellen Wasserstand. Andere Kennwerte der API (z. B. HHW, NW)
werden nicht ausgegeben. Reihenfolge: MNW, MW, MHW, HSW, GlW, Aktuell.

```text
Kennwerte: Heidelberg UP (NECKAR, km 26,1)
MNW: 207 cm
MW: 220 cm
MHW: 401 cm
HSW: 260 cm
Aktuell: 208 cm
```

Fehlende Kennwerte werden übersprungen. Bei mehreren Treffern gelten dieselben
Regeln wie bei `stand`. Kein Treffer: Exit 1.

Optionen: `--erster` wie bei `stand`.

### `pegel watch ORT [--ueber CM | --unter CM]`

Liest den aktuellen Wert, vergleicht ihn mit dem lokal gespeicherten letzten
Wert und prüft optional eine Schwelle. Es wird nichts an die WSV gesendet.

Textausgabe (Beispiel):

```text
Watch: Heilbronn Schleuse UP (NECKAR, km 113,3)
Aktuell: 221 cm
Seit letztem Aufruf: 0 cm
Schwelle: über 300 cm
Status: unter Schwelle
```

- Erster Aufruf ohne gespeicherten Wert: `Seit letztem Aufruf: erster Aufruf`.
- `--ueber CM`: Schwelle gilt als überschritten, wenn der aktuelle Wert
  größer oder gleich `CM` ist.
- `--unter CM`: Schwelle gilt als überschritten, wenn der aktuelle Wert
  kleiner oder gleich `CM` ist.
- `--ueber` und `--unter` schließen sich gegenseitig aus (Exit 2).
- Ohne Schwelle wird nur die Änderung seit dem letzten Aufruf gemeldet.
- Der Zustand wird nach jeder erfolgreichen Abfrage aktualisiert. Das
  Überschreiten einer Schwelle ist kein Fehler: Exit 0. Der Zustand steht im
  JSON-Feld `ueberschritten` und im Text.
- Pro Pegel wird ein Zustandseintrag gespeichert (UUID als Schlüssel).

Optionen:

| Option | Bedeutung |
|---|---|
| `--ueber CM` | Obere Schwelle in Zentimetern. |
| `--unter CM` | Untere Schwelle in Zentimetern. |

## JSON-Ausgabe

Mit `--json` oder bei nicht-TTY stdout steht genau ein JSON-Objekt auf stdout.
Grundschema:

```json
{"befehl": "stand", "pegel": {"name": "...", "gewaesser": "...", "km": 113.3}, "wasserstand_cm": 221.0, "zeit": "2026-11-13T09:15:00+01:00", "einordnung": {"nsw_hsw": "normal", "mnw_mhw": "unknown"}, "trend_3h_cm": 0.0}
```

| Befehl | Wichtige Felder |
|---|---|
| `suche` | `befehl`, `treffer` (Liste mit `name`, `gewaesser`, `km`, `wasserstand_cm`, `einheit`, `zeit`) |
| `stand` | `befehl`, `pegel`, `wasserstand_cm`, `einheit`, `zeit`, `einordnung.nsw_hsw`, `einordnung.mnw_mhw`, `trend_3h_cm` |
| `verlauf` | `befehl`, `pegel`, `tage`, `min_cm`, `max_cm`, `aktuell_cm`, `einheit`, `punkte`, `werte` (Liste aus `zeit`, `wasserstand_cm`) |
| `fluss` | `befehl`, `gewaesser`, `anzahl`, `pegel` (Liste wie bei `suche`) |
| `kennwerte` | `befehl`, `pegel`, `kennwerte` (Objekt Kürzel → Wert in cm), `aktuell_cm`, `einheit` |
| `watch` | `befehl`, `pegel`, `aktuell_cm`, `aenderung_cm`, `erster_aufruf`, `schwelle` (`ueber`/`unter` oder `null`), `ueberschritten` |

Fehler mit `--json` liefern ebenfalls genau ein JSON-Objekt:

```json
{"fehler": "PEGELONLINE nicht erreichbar", "naechster_schritt": "Später erneut versuchen oder PEGEL_BASE_URL prüfen"}
```

## Umgebungsvariablen und Pfade

| Variable | Bedeutung |
|---|---|
| `PEGEL_BASE_URL` | Basis-URL der API, Standard `https://www.pegelonline.wsv.de/webservices/rest-api/v2`. Für Fake-Server und Tests. Ungültige URL: Exit 2. |
| `PEGEL_HEUTE` | `JJJJ-MM-TT`, nur für deterministische Tests. Überschreibt das Bezugsdatum für relative Angaben in `watch`; ohne Wirkung auf Messzeitpunkte aus der API. |
| `XDG_CACHE_HOME` | Basis für den Cache; Standard `~/.cache`. Cache-Verzeichnis: `$XDG_CACHE_HOME/pegel-cli`. |
| `XDG_STATE_HOME` | Basis für Watch-Zustand; Standard `~/.local/state`. Verzeichnis: `$XDG_STATE_HOME/pegel-cli`. |
| `NO_COLOR` | Deaktiviert Farbausgabe, sofern vorhanden. |

Cache: GET-Antworten werden fünf Minuten wiederverwendet (Dateien unter
`~/.cache/pegel-cli`, Verzeichnis mit Benutzerrechten). Watch-Zustand:
`~/.local/state/pegel-cli/watch.json`, Datei mit Rechten `0600`, Verzeichnis
`0700`. Beide Pfade respektieren die XDG-Variablen.

Netzwerk: nur `GET`, Timeout 10 Sekunden, User-Agent
`pegel-cli/0.1 (+https://github.com/smlfg/pegel-cli)`. Es werden keine Cookies
und keine Zugangsdaten gespeichert.

## Exit-Codes

| Code | Bedeutung |
|---|---|
| `0` | Erfolg, auch bei leerer Suche oder nicht überschrittener/überschrittener Watch-Schwelle. |
| `1` | Kein Treffer oder sonstiger Fehler, der nicht Usage/Netz ist. Fehlermeldung nennt den nächsten Schritt. |
| `2` | Usage: unbekanntes Unterkommando, fehlendes Argument, ungültige Zahl, widersprüchliche Optionen oder mehrdeutiger Treffer ohne TTY/`--erster`. |
| `3` | Netzwerk- oder Quellfehler: DNS, Timeout, HTTP-Fehler, ungültiges JSON der API. |
| `4` | Login/Authentifizierung nötig. Bei `pegel` derzeit nicht verwendet, da die API offen ist. |
| `130` | Abbruch durch Strg+C. Kein Traceback. |

Auch bei Usage-Fehlern mit `--json` steht genau ein JSON-Objekt auf stdout.
Bei EOF oder Strg+C gibt es keinen Traceback; die Meldung nennt den nächsten
Schritt.

## Textformat

- Ganze Zentimeter ohne Nachkommastelle, Einheit `cm`.
- Kilometer mit einer Nachkommastelle und Dezimalkomma (`km 113,3`).
- Messzeitpunkte als `DD.MM.YYYY HH:MM` in der Zeitzone der API.
- Gewässer- und Pegelnamen wie von der API geliefert (Kurzname des Pegels,
  Gewässer in Großschreibung).
- Nummerierte Listen beginnen bei `1)`.

## Nicht Teil dieser Schnittstelle

- Kein `login`, `logout` oder `whoami`.
- Keine schreibenden Aktionen, keine Formulare, keine Bestätigung `[j/N]`.
- Kein Push, keine E-Mail, keine Benachrichtigung.
