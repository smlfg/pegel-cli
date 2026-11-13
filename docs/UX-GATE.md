# UX-Gate-Bericht

- Datum: 13.11.2026
- Repo: `smlfg/pegel-cli`
- Tool: `pegel`
- Modus: voll

## Ergebnis

| Prüfung | Befehl | Exit |
|---|---|---|
| Statisch und Sitzungen | `python3 tests/harness/ux_check.py .` | 0 |
| Interaktive Sitzungen | `python3 tests/harness/ux_session.py .` | 0 |

Beide Läufe sind grün (kein FAIL, `UX09` SKIP, weil das Tool read-only ist).
Ergänzend: `pytest -q` -> `60 passed`.

## ux_check.py

| ID | Ergebnis | Befund |
|---|---|---|
| UX00 | PASS | 7 Request(s) am Fake-Server, keine Fremdverbindung |
| UX01 | PASS | docs/UX.md: 5 Sitzungen, 0 formsteps |
| UX02 | PASS | keine Credential-Env-Variablen gefunden |
| UX03 | PASS | --help, --version und 6 Unterkommandos mit Exit 0 |
| UX04 | PASS | 6 Unterkommandos ohne Pflicht-Option statt positional |
| UX05 | PASS | 5 Sitzungen ohne JSON/Traceback im TTY |
| UX06 | PASS | Schnellstart: 5 Tool-Befehle, Installation passt |
| UX07 | PASS | keine ux-formsteps, keine schreibende Aktion |
| UX08 | PASS | keine ux-formsteps, keine schreibende Aktion |
| UX09 | SKIP | keine schreibende Sitzung |

## ux_session.py

| Sitzung | Lauf | Ergebnis | Befund |
|---|---|---|---|
| Installation und erster Wasserstand | 1 | PASS | OK |
| Pegel nach Ortsnamen suchen | 1 | PASS | OK |
| Alle Pegel eines Flusses | 1 | PASS | OK |
| Verlauf der letzten Tage | 1 | PASS | OK |
| Kennwerte eines Pegels | 1 | PASS | OK |
