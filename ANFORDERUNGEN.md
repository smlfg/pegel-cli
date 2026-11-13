# Anforderungen: pegel

## Zweck

`pegel` bringt die aktuellen Wasserstände der Bundeswasserstraßen ins
Terminal. Das Werkzeug fragt die offene PEGELONLINE-REST-API der
Wasserstraßen- und Schifffahrtsverwaltung des Bundes (WSV) lesend ab und
bereitet die Daten für Menschen und Agenten auf: Pegel per Ortsname finden,
Wasserstand mit Einordnung und Trend sehen, Verläufe und Kennwerte abrufen,
alle Pegel eines Flusses auflisten und lokale Schwellen beobachten.

Das Tool ist ausdrücklich **read-only**. Es gibt keinen Login, keine
schreibende Web-Aktion und keine Änderung an Daten der WSV.

## Nutzer-Aufgaben

| Nutzergruppe | Aufgabe | Befehl |
|---|---|---|
| Wassersportler, Kanuten | Ist der Pegel gerade niedrig, normal oder hoch? | `pegel stand ORT` |
| Schiffer | Wie hat sich der Wasserstand in den letzten Stunden entwickelt? | `pegel verlauf ORT --tage N` |
| Anwohner bei Hochwasser | Welche Pegel am Fluss sind auffällig? | `pegel fluss NAME --nur-hoch` |
| Planung, Einordnung | Wo liegen MNW, MW, MHW, HSW und GlW? | `pegel kennwerte ORT` |
| Beobachtung | Hat sich seit dem letzten Aufruf etwas getan oder wurde eine Schwelle überschritten? | `pegel watch ORT --ueber CM` |
| Agenten | Maschinenlesbare Antwort ohne Terminal-Formatierung | `--json` bzw. Pipe |

Die wichtigsten Aufgaben sind in `docs/UX.md` als abtippbare Sitzungen
festgehalten. Orts- und Flussnamen werden positional übergeben; IDs oder
Pflicht-Optionen sind für die Kernaufgaben nicht nötig.

## Nachfrage

Stand: **13.11.2026**, Demand-Gate aus `scratch/ref/NEXT20.md`, Platz 12.

- GitHub-Suche nach `pegel mcp`, `pegelonline cli` und `wasserstand mcp`:
  **0 Treffer**. Es gibt damit kein etabliertes CLI und keinen MCP-Server für
  diese Aufgabe.
- Vorhandene Nutzung liegt in Bibliotheken und Integrationen:
  `aiopegelonline` für Home Assistant und `ioBroker.pegelonline`. Die
  Nachfrage ist über Smart-Home-Nutzer belegt, für Agenten und Terminal-Nutzer
  aber noch nicht durch ein Werkzeug abgedeckt.
- Einordnung der Routine: **GO 13.11.2026**, Nachfrage **schwach**, aber
  Nachfragebeleg über die Home-Assistant-/ioBroker-Integrationen vorhanden.

## Datenquelle

- API: PEGELONLINE REST-API v2 der WSV,
  `https://www.pegelonline.wsv.de/webservices/rest-api/v2`
- Datenlizenz: **DL-DE/Zero** (Deutschland – Datenlizenz Deutschland Zero).
- Genutzte lesende Endpunkte:
  - `GET /stations.json` mit `fuzzyId`, `waters`,
    `includeTimeseries=true`, `includeCurrentMeasurement=true`
  - `GET /waters.json`
  - `GET /stations/{uuid|name}/W.json` mit
    `includeCurrentMeasurement=true&includeCharacteristicValues=true`
  - `GET /stations/{uuid}/W/measurements.json?start=P1D` bis `P30D`
- Die Basis-URL ist über `PEGEL_BASE_URL` überschreibbar. Das ist für
  Fake-Server in Tests und für Gate-Läufe vorgesehen.
- Live erkundet am 13.11.2026 mit lesenden GET-Requests (HTTP 200, JSON, kein
  Bot-Schutz). Antworten und Notizen liegen unter `scratch/live/`, gekürzte
  Fixtures unter `tests/fixtures/ux/`.

## Funktionale Anforderungen

- **FA-01 Suche:** `pegel suche ORT` sucht case-insensitiv über `fuzzyId` und
  zeigt nummeriert Name, Gewässer, Kilometer und aktuellen Wert. Umlaute
  werden URL-kodiert unterstützt.
- **FA-02 Stand:** `pegel stand ORT` zeigt Pegelname, Gewässer, Kilometer,
  Wasserstand mit Einheit, Messzeitpunkt, Einordnung (niedrig/normal/hoch bzw.
  unbekannt für MNW/MHW und NSW/HSW) und den Trend der letzten drei Stunden.
  Bei mehreren Treffern gibt es im TTY eine nummerierte Auswahl, für Agenten
  `--erster` oder eine Liste mit Exit 2.
- **FA-03 Verlauf:** `pegel verlauf ORT [--tage N]` zeigt Minimum, Maximum,
  aktuellen Wert und die Anzahl der Messpunkte. Standard ist ein Tag; die API
  liefert etwa 30 Tage.
- **FA-04 Fluss:** `pegel fluss NAME` löst den Flussnamen über `/waters.json`
  auf (auch mit Tippfehlern) und listet die Pegel flussabwärts nach Kilometer.
  `--nur-hoch` filtert auf hohe Wasserstände.
- **FA-05 Kennwerte:** `pegel kennwerte ORT` zeigt MNW, MW, MHW, HSW und – falls
  vorhanden – GlW mit Einheit sowie den aktuellen Wert.
- **FA-06 Watch:** `pegel watch ORT [--ueber CM|--unter CM]` speichert den
  letzten Wert lokal, meldet die Änderung seit dem letzten Aufruf und ob eine
  Schwelle über- oder unterschritten wurde. Es wird nichts an die WSV gesendet.
- **FA-07 Ausgabe:** Im Terminal lesbarer Text mit deutschen Zahlen (Komma bei
  Kilometern), JSON nur mit `--json` oder wenn stdout kein TTY ist.
- **FA-08 Konfiguration:** Basis-URL über `PEGEL_BASE_URL`; Cache und
  Watch-Zustand unter den XDG-Pfaden, Watch-Zustand mit Rechten 0600.
- **FA-09 Höflichkeit:** eigener User-Agent mit Repo-URL, Timeout, Cache von
  fünf Minuten für GET-Antworten.
- **FA-10 Fehler:** jede Fehlerklasse hat einen festen Exit-Code, Fehlermeldungen
  nennen den nächsten Schritt, keine Tracebacks – auch nicht bei Strg+C oder
  EOF.

## Nicht-funktionale Anforderungen

- Python **>= 3.10**; Abhängigkeiten nur `argparse` und `httpx` oder `requests`
  (plus `beautifulsoup4`, falls es für HTML nötig wäre; die API liefert JSON).
- Installation über `pipx install git+https://github.com/smlfg/pegel-cli`,
  Konsolenskript `pegel`.
- Lizenz MIT, Copyright smlfg; Daten unter DL-DE/Zero.
- Keine Secrets, keine echten Personendaten in Repository, Fixtures oder Logs.
- Tests erreichen nie echte Server, sondern ausschließlich Fake-Server über
  `PEGEL_BASE_URL`.

## Grenzen

- **Inoffiziell:** `pegel` ist kein Angebot der WSV und nicht mit ihr
  verbunden. Die API kann sich ändern, gedrosselt werden oder ausfallen.
- **Nur lesend live getestet:** Am 13.11.2026 wurden ausschließlich lesende
  GET-Requests gegen öffentliche Seiten ausgeführt. Es gibt keine Garantie für
  Verfügbarkeit, Vollständigkeit oder Aktualität der Daten.
- **Kein Login, keine Schreibaktion:** Es werden keine Konten angelegt und
  keine Daten verändert.
- **Datenqualität:** Einordnung und Kennwerte stammen aus der API; fehlende
  Werte werden als „unbekannt“ ausgegeben, nicht geschätzt.
- **Verlauf:** maximal etwa 30 Tage (`P30D`), Auflösung 15 Minuten.
- **Watch:** beobachtet nur lokal; es gibt keine Benachrichtigung, keinen
  Server-Job und keinen Versand von Nachrichten.

## Akzeptanzkriterien

Jede Sitzung aus `docs/UX.md` hat mindestens einen Test in
`tests/acceptance/test_ux_sessions.py`. Die Tests starten das Tool als
Subprozess gegen den Fake-Server mit den `ux-routes` und prüfen die
Kernausgaben:

1. Installation und `pegel stand Heilbronn` – Pegel, Wasserstand, Stand,
   Einordnung, Trend, Exit 0.
2. `pegel suche Mannheim` – beide Treffer mit Gewässer, Kilometer und Wert.
3. `pegel fluss Neckar` – fünf Pegel in Kilometerreihenfolge.
4. `pegel verlauf Heilbronn --tage 1` – Minimum, Maximum, aktueller Wert,
   Punkte, Exit 0.
5. `pegel kennwerte Heidelberg` – MNW, MW, MHW, HSW, aktueller Wert.

Zusätzlich gilt: `python3 tests/harness/ux_check.py . --spec-only` endet mit
Exit 0, und `--json` liefert auf stdout genau ein JSON-Objekt.
