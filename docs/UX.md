# UX-Spec: pegel

Live-Wasserstände der Bundeswasserstraßen über die offene PEGELONLINE-REST-API
der WSV. Die Daten stehen unter DL-DE/Zero. Das Tool ist read-only: es gibt
keinen Login und keine schreibende Aktion.

```ux-meta
{"tool": "pegel",
 "install": "pipx install git+https://github.com/smlfg/pegel-cli",
 "base_url_env": "PEGEL_BASE_URL",
 "env": {}}
```

## Sitzungen

### Installation und erster Wasserstand

Die Installation landet mit dem Konsolenskript `pegel` im PATH. Danach reicht
ein Ortsname positional; das Tool wählt bei einem eindeutigen Treffer direkt
den Pegel und zeigt Wasserstand, Einordnung und Trend der letzten drei Stunden.

```ux-session
$ pipx install git+https://github.com/smlfg/pegel-cli
$ pegel stand Heilbronn
< Pegel: Heilbronn Schleuse UP (NECKAR, km 113,3)
< Wasserstand: 221 cm
< Stand: 13.11.2026 09:15
< Einordnung: normal (NSW/HSW), MNW/MHW unbekannt
< Trend (3 h): 0 cm
! exit 0
```

### Pegel nach Ortsnamen suchen

Der Suchbegriff ist positional und wird ohne Umlaut-Schreibweise gefunden.
Mehrere Treffer erscheinen nummeriert mit Fluss, Kilometer und aktuellem Wert,
damit ein Mensch ohne Nachschlagen weiterarbeiten kann.

```ux-session
$ pegel suche Mannheim
< 1) MANNHEIM (RHEIN, km 424,7): 145 cm
< 2) Mannheim Neckar (NECKAR, km 3,1): 146 cm
! exit 0
```

### Alle Pegel eines Flusses

Der Flussname wird positional übergeben; das Tool löst ihn über die
Gewässerliste auf und listet die zugehörigen Pegel flussabwärts.

```ux-session
$ pegel fluss Neckar
< NECKAR: 5 Pegel
< 1) Mannheim Neckar (km 3,1): 146 cm
< 2) Feudenheim Schleuse UP (km 6,1): 133 cm
< 3) Ladenburg Wehr UP (km 11,9): 685 cm
< 4) Schwabenheim Schleuse UP (km 17,6): 214 cm
< 5) Heidelberg UP (km 26,1): 208 cm
! exit 0
```

### Verlauf der letzten Tage

Der Verlauf zeigt Minimum, Maximum und den aktuellen Wert. Die Anzahl der
Tage ist optional (`--tage N`, Standard 1). Die Ausgabe bleibt im Terminal
lesbar; JSON gibt es nur mit `--json` oder bei einer Pipe.

```ux-session
$ pegel verlauf Heilbronn --tage 1
< Verlauf: Heilbronn Schleuse UP (NECKAR), letzte 24 h
< Minimum: 216 cm
< Maximum: 228 cm
< Aktuell: 221 cm
< Punkte: 95
! exit 0
```

### Kennwerte eines Pegels

Die Kennwerte kommen aus derselben offenen API und werden mit Einheit und
Bezugszeitraum ausgegeben.

```ux-session
$ pegel kennwerte Heidelberg
< Kennwerte: Heidelberg UP (NECKAR, km 26,1)
< MNW: 207 cm
< MW: 220 cm
< MHW: 401 cm
< HSW: 260 cm
< Aktuell: 208 cm
! exit 0
```

## Lesende Routen

Alle Sitzungen kommen mit lesenden GET-Requests aus. Die Fixtures sind aus
echten Live-Antworten vom 13.11.2026 gekürzt; Orts- und Gewässernamen sind
öffentliche Daten. `path` wird ohne Querystring verglichen, `query_contains`
unterscheidet die Aufrufe auf `/stations.json`.

```ux-routes
[{"method":"GET","path":"/stations.json","query_contains":"fuzzyId=heilbronn","response":"tests/fixtures/ux/stations_heilbronn.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/stations.json","query_contains":"fuzzyId=mannheim","response":"tests/fixtures/ux/stations_mannheim.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/stations.json","query_contains":"fuzzyId=heidelberg","response":"tests/fixtures/ux/stations_heidelberg.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/stations.json","query_contains":"waters=NECKAR","response":"tests/fixtures/ux/stations_neckar.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/waters.json","response":"tests/fixtures/ux/waters.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/stations/f77df170-d23a-451c-9c43-b1580ccd3e2c/W/measurements.json","query_contains":"start=P1D","response":"tests/fixtures/ux/heilbronn_messungen_p1d.json","status":200,"content_type":"application/json; charset=utf-8"},
 {"method":"GET","path":"/stations/827b2685-47ec-44df-a90f-980f5e0c1591/W.json","query_contains":"includeCharacteristicValues=true","response":"tests/fixtures/ux/heidelberg_w.json","status":200,"content_type":"application/json; charset=utf-8"}]
```

## Schreibende Aktion

Es gibt keine. Das Tool liest nur öffentliche Wasserstandsdaten; deshalb sind
`ux-formsteps`, `credential_env` und ein `login`-Befehl nicht nötig. `watch`
speichert lediglich lokal den zuletzt gesehenen Wert und sendet nichts.
