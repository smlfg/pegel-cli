# Pflicht-QA: pegel

Datum: 13.11.2026, ca. 13:25–13:40 (Europe/Berlin)
Version: `pegel 0.1.0`
Commit: `2799ef0f49ab6191f4533bc51340183724896923`
Installation: `pipx install git+https://github.com/smlfg/pegel-cli` in
`scratch/pipx`, Python 3.14.7. Die installierte `direct_url.json` nennt
denselben Commit wie `HEAD`.
Live-Quelle: PEGELONLINE REST-API v2, nur lesende GET-Requests.
Tests: `scratch/venv/bin/pytest -q` -> `60 passed`.

Hinweis: Live-Messwerte liegen im 15-Minuten-Raster. Vergleiche wurden gegen
jeweils frische Rohdaten geführt; einzelne Werte können sich zwischen zwei
Abfragen ändern. Die Live-Ausgabe von `pegel fluss Neckar` enthält 43 Pegel;
die UX-Fixture ist für die Sitzung auf 5 Pegel gekürzt. Das ist kein Fehler.

| Nr | Prüfung | Befehl | Erwartet | Ergebnis | Beleg (gekürzt) |
|---:|---|---|---|---|---|
| 1 | Frische pipx-Installation | `pipx install git+https://github.com/smlfg/pegel-cli` (Orchestrator) | Erfolg, App `pegel` | OK | `scratch/qa/pipx-install.log`: `pegel-cli 0.1.0`, App `pegel` |
| 2 | Installierter Commit | `PIPX_HOME=scratch/pipx pipx list`, `direct_url.json` | Commit = HEAD | OK | `2799ef0f49ab…` in `direct_url.json` und `git rev-parse HEAD` |
| 3 | Version über PATH | `PATH=scratch/pipx/bin:$PATH pegel --version` | `pegel 0.1.0`, Exit 0 | OK | `pegel 0.1.0` |
| 4 | Haupt-Hilfe | `pegel --help` | Exit 0, alle Unterkommandos | OK | Exit 0; suche, stand, verlauf, fluss, kennwerte, watch |
| 5 | README `stand` im TTY | `script -qec "pegel stand Heilbronn" …` | Text, Exit 0 | OK | Heilbronn Schleuse UP, 212 cm, 13.11.2026 13:15, Trend -8 cm |
| 6 | README `suche` im TTY | `script -qec "pegel suche Mannheim" …` | Trefferliste, Exit 0 | OK | MANNHEIM 146 cm; Mannheim Neckar 148 cm |
| 7 | README `fluss` im TTY | `script -qec "pegel fluss Neckar" …` | Pegel flussabwärts, Exit 0 | OK | `NECKAR: 43 Pegel`; km 3,1 bis 202,6 aufsteigend |
| 8 | README `verlauf` im TTY | `script -qec "pegel verlauf Heilbronn --tage 1" …` | Text, Exit 0 | OK | Minimum 212, Maximum 228, Aktuell 212, 96 Punkte |
| 9 | README `kennwerte` im TTY | `script -qec "pegel kennwerte Heidelberg" …` | Text, Exit 0 | OK | MNW 207, MW 220, MHW 401, HSW 260, Aktuell 209 |
| 10 | README `watch` im TTY | `script -qec "pegel watch Heilbronn --ueber 300" …` | Text, Exit 0 | OK | Erster Aufruf, 212 cm, Status unter Schwelle |
| 11 | Fake-Server, alle Aktionen | `PEGEL_BASE_URL=…` mit den `ux-routes` | UX-Ausgaben, Exit 0 | OK | 221 cm, 2 Treffer, 5 Pegel, 95 Punkte, Kennwerte, Watch |
| 12 | Fake-Server, Requests | Request-Log nach 6 Aktionen | nur GET, keine Fremdhosts | OK | 10 Requests, alle GET, Pfade/Queries passen zu `ux-routes` |
| 13 | Suche semantisch | `pegel suche Mannheim --json` gegen Rohdaten | Treffer, Werte, km stimmen | OK | MANNHEIM 146 cm/km 424,733; Mannheim Neckar 148 cm/km 3,1 |
| 14 | Fluss semantisch | `pegel fluss Neckar --json` gegen Rohdaten | gleiche Pegel, sortiert | OK | 43/43 Namen und km gleich; km monoton; Werte teils 13:15/13:30 |
| 15 | Filter `--nur-hoch` live | `pegel fluss Neckar --nur-hoch --json` | nur hohe Pegel, hier 0 | OK | Tool 0; Rohdaten: 43 Pegel, 0 mit `high` |
| 16 | Filter `--nur-hoch` nicht leer | `PEGEL_BASE_URL=… pegel fluss Testfluss --nur-hoch --json` | genau die hohen Pegel | OK | 2 von 5: A (MNW high), B (NSW high); C/D/E nicht enthalten |
| 17 | Stand semantisch | `pegel stand Heilbronn --json` gegen Rohdaten | Wert, Zeit, Einordnung | OK | 212 cm, 13:15, NSW/HSW normal, MNW/MHW unknown |
| 18 | Trend semantisch | Messwert 3 h vorher vergleichen | Differenz -8 cm | OK | 212 − 220 = −8; Feld `trend_3h_cm` = -8 |
| 19 | Verlauf 1 Tag | `pegel verlauf Heilbronn --tage 1 --json` | 96 Punkte, min/max/aktuell | OK | 96 Punkte, 212/228/212, Zeitstempel identisch mit Rohdaten |
| 20 | Verlauf 2 Tage | `pegel verlauf Heilbronn --tage 2 --json` | 192 Punkte in 48 h | OK | 192 Punkte, 47,75 h Spanne, alle Zeitstempel im Fenster |
| 21 | Kennwerte semantisch | `pegel kennwerte Heidelberg --json` gegen Rohdaten | Kennwerte stimmen | OK | 207/220/401/260; Aktuell 209, Rohdaten 13:30 = 210 |
| 22 | Umlaute | `pegel suche Köln --json`, `pegel suche KÖLN --json` | je 1 Treffer | OK | KÖLN, RHEIN, km 688 |
| 23 | Tippfehler Fluss | `pegel fluss Neckr --json` | NECKAR | OK | NECKAR, 43 Pegel; auch `neckar` und `Neckar` geprüft |
| 24 | Leere Suche | `pegel suche Qqqzzz --json` | Exit 0, leere Liste | OK | `{"befehl":"suche","treffer":[]}`; Text nennt nächsten Schritt |
| 25 | Kein Treffer `stand` | `pegel stand Qqqzzz --json` | Exit 1, nächster Schritt | OK | `Kein Pegel zu 'Qqqzzz' gefunden.` + `naechster_schritt` |
| 26 | Unbekanntes Gewässer | `pegel fluss Qqqzzz --json` | Exit 1, nächster Schritt | OK | `Gewässer 'Qqqzzz' nicht gefunden.` + `naechster_schritt` |
| 27 | Watch erster Aufruf | `pegel watch Heilbronn --ueber 300 --json` | erster Aufruf, Exit 0 | OK | `erster_aufruf:true`, `aenderung_cm:null`, `ueberschritten:false` |
| 28 | Watch Änderung | Zustand auf 222 setzen, dann `watch --json` | Änderung -10 | OK | `aenderung_cm:-10.0`, `erster_aufruf:false` |
| 29 | Watch Schwellen | `--ueber 212`, `--ueber 213`, `--unter 212`, `--unter 211` | `>=` bzw. `<=` korrekt | OK | true / false / true / false |
| 30 | Watch Konflikt | `pegel watch Heilbronn --ueber 1 --unter 2 --json` | Exit 2, JSON | OK | argparse: „not allowed with“; JSON `Ungültige Eingabe.` |
| 31 | Watch-Zustand Rechte | `stat` auf Zustandsdatei | Datei 0600, Verzeichnis 0700 | OK | `600 …/watch.json`, `700 …/pegel-cli` |
| 32 | Netzfehler | `PEGEL_BASE_URL=http://127.0.0.1:1 pegel stand Heilbronn --json` | Exit 3, nächster Schritt | OK | `Connection refused`, Exit 3, kein Traceback |
| 33 | Ungültige Basis-URL | `PEGEL_BASE_URL=notaurl pegel stand Heilbronn --json` | Exit 2, nächster Schritt | OK | `PEGEL_BASE_URL ist keine gültige http(s)-URL` |
| 34 | JSON valide | `--json` für alle Befehle und Fehlerfälle | genau ein gültiges Objekt | OK | `python3 -m json.tool` für alle Ausgaben erfolgreich |
| 35 | Auto-JSON bei Pipe | `pegel suche Mannheim` in Pipe | JSON ohne `--json` | OK | Ausgabe beginnt mit `{"befehl":"suche",…}` |
| 36 | Mehrdeutig / `--erster` | `pegel stand Mannheim`, dann `--erster` | Exit 2 + Treffer; `--erster` Exit 0 | OK | Fehler-JSON mit 2 Treffern; `--erster` wählt MANNHEIM |
| 37 | TTY-Auswahl | `pegel stand Mannheim` mit 2, 9, EOF | gültig Exit 0; sonst Exit 2 | OK | 2 -> Mannheim Neckar; 9/EOF -> Meldung + nächster Schritt |
| 38 | Strg+C bei Auswahl | pty sendet SIGINT direkt nach `Auswahl [1-2]:` | Exit 130 | FAIL | Exit 2, „Keine Auswahl getroffen.“; kein Traceback. Details in `scratch/QA-FAILS.md` |
| 39 | `--tage` ungültig | `--tage 0`, `--tage 31`, `--tage abc` | Exit 2, nächster Schritt | OK | 0/31 mit Bereichsfehler; abc mit JSON `Ungültige Eingabe.` |
| 40 | Usage-Fehler | `pegel`, `pegel quatsch --json`, `pegel stand --json` | Exit 2, JSON valide | OK | JSON-Fehler auf stdout, Usage auf stderr |
| 41 | Pipe-Abbruch | Ausgabe von `pegel fluss Neckar` an `head -1` | Exit 0, kein Traceback | OK | PIPESTATUS 0 0; stderr leer |
| 42 | Unterkommandos `--help` | `pegel <befehl> --help` für alle 6 | Exit 0 | OK | alle Exit 0 |
| 43 | Text statt JSON im TTY | alle 6 Befehle per `script -qec` | lesbarer Text | OK | Logs `scratch/qa/01…06` und `07…12` |
| 44 | Fehler nennen nächsten Schritt | Netz-, Treffer- und Bereichsfehler | Meldung mit nächstem Schritt | OK | „Nächster Schritt: …“ in Text und JSON |
| 45 | Testsuite | `scratch/venv/bin/pytest -q` | grün | OK | `60 passed` |
| 46 | Cache | `pegel suche Mannheim` zweimal, gleiche `XDG_CACHE_HOME` | 1 Request, Rechte 700/600 | OK | 2 Läufe -> 1 Request; Verzeichnis 700, Datei 600 |

## Zählung

- OK: 45
- FAIL: 1
- Gesamt: 46

## Offene FAILs

1. **Nr. 38 – Strg+C bei der Pegel-Auswahl liefert Exit 2 statt 130.**
   Erwartet laut README/INTERFACE: Abbruch mit Strg+C = Exit 130. Tatsächlich
   fängt die Auswahl die Unterbrechung als Usage-Fehler ab und beendet mit
   Exit 2. Es gibt keinen Traceback und die Meldung nennt einen nächsten
   Schritt; nur der Exit-Code weicht ab. Reproduktion und Ausgabe stehen in
   `scratch/QA-FAILS.md`. Gemäß QA-Rolle wurde der Code nicht geändert.

## Weitere Hinweise

- Alle Live-Aufrufe waren lesend (GET). Die einzigen Schreibzugriffe waren
  Cache und Watch-Zustand unter `scratch/qa/`, nicht im Repo.
- Die README-Installationszeile wurde vom Orchestrator ausgeführt; das
  Protokoll und die installierte `direct_url.json` wurden geprüft, die
  Installation nicht erneut verändert.
- Keine Zugangsdaten, keine personenbezogenen Daten und keine Secrets in
  diesem Bericht oder in den getesteten Ausgaben.
- Es wurde nicht gepusht.
