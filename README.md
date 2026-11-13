# pegel

Live-Wasserstände der Bundeswasserstraßen im Terminal: Pegel per Ortsname
finden, aktuellen Stand mit Einordnung und Trend sehen, Verlauf und Kennwerte
abrufen sowie alle Pegel eines Flusses auflisten. Quelle ist die offene
PEGELONLINE-REST-API der WSV (Datenlizenz DL-DE/Zero), ohne Login.

## Schnellstart

```bash
pipx install git+https://github.com/smlfg/pegel-cli
pegel stand Heilbronn
pegel fluss Neckar
```

Weitere Befehle: `pegel suche ORT`, `pegel verlauf ORT --tage N`,
`pegel kennwerte ORT` und `pegel watch ORT --ueber CM`. Für Agenten gibt es
`--json`; im Terminal ist die Ausgabe lesbar formatiert.

## Daten und Lizenz

Die Wasserstandsdaten stammen von PEGELONLINE (WSV) und stehen unter
DL-DE/Zero. Der Code steht unter der MIT-Lizenz, Copyright smlfg.
