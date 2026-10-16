# Europäische Sprachprofile · 1.4.3-europe-preview.1

Ausgangspunkt ist der unveränderte Release 1.4.2 (Commit 5843925).
Die parallele PT-BR-Entwicklung ist in dieser separaten Arbeitskopie nicht enthalten.
Diese Preview ersetzt keine abgeschlossene Veröffentlichung mit vollständigem Spieldurchlauf.

## Integriert

| Edition | Neue Sprachen | Dialogeinträge je Profil |
|---|---|---|
| Rot | Spanisch | 2.595 |
| Gelb | Spanisch | 2.710 |
| Gold | Spanisch, Französisch, Italienisch | 4.331 / 4.362 / 4.362 |
| Silber | Spanisch, Französisch | 4.331 / 4.362 |
| Kristall | Spanisch, Italienisch | 5.523 / 4.863 |
| Feuerrot | Spanisch, Italienisch | 9.063 von 9.066 nativen Textschlüsseln |
| Blattgrün | Spanisch, Französisch | 9.063 von 9.066 nativen Textschlüsseln |

Smaragd FR/IT/ES war bereits enthalten. Damit sind alle 16 bereitgestellten
Sprach-ROMs berücksichtigt: 13 neue und drei bestehende europäische Profile.
Zusammen mit Deutsch sind 27 zusätzliche Sprach-ROM-Profile registriert.
Englisch bleibt die jeweilige US-Basis. Die neun Sprachen der Mod-Oberfläche
sind davon unabhängig.

Für GB/GBC enthalten die Profile Dialogrezepte, Schrift, Pokémon-, Attacken-,
Item-, Trainerklassen- und Typnamen. Gen2 ergänzt Attacken-/Itembeschreibungen,
495 bzw. 541 einzelne Trainernamen, 95 bzw. 96 Ortsnamen und 251 Pokédex-Einträge.
Die 889 bzw. 1.011 benannten Gen2-Systemtexte sind vollständig zugeordnet.
70 kurze, neu verfasste UI-Übersetzungen pro Sprache ergänzen die ROM-Daten.
Italienisches Kristall enthält im Original leere, ungenutzte Mobiladapter-Texte;
deshalb unterscheiden sich Textzahlen und Inhalt zwischen den Regionen.
Metrische Pokédex-Werte ergänzen ausschließlich Anzeigefelder; die ursprünglichen
US-Gewichte und alle Kampfwerte bleiben erhalten.

Die neuen Feuerrot-/Blattgrün-Profile wurden gegen vier byteidentisch
rekonstruierte Handelsfassungen abgeglichen. Ihre Text-, Grafik- und Weltprofile
werden aus geprüften ELF-Symbolen und Tabellenstrukturen abgeleitet.
GB/GBC verwenden exakte ROM-Prüfsummen, rekonstruierte Symboltabellen,
Map-/Event-/Skript-Vergleiche und abgeglichene Textbank-Grenzen.
Das ist eine Prüfung der zugeordneten Daten, kein Beweis für jedes Spielereignis.

## Noch offen innerhalb dieser Profile

- GB/GBC: vollständige Übersetzung der zusätzlich vom Recompiler verfassten
  Menü-, Kampf-, Online-, Einstellungs- und Hilfetexte. Die 70 UI-Einträge sind
  ein Anfang; englische Laufzeittexte sind weiterhin zu erwarten.
- GB/GBC: lokalisierte Titel-/Menü-/Statusgrafiken, Weltschilder, Namenseingabe
  und alle regionalen Layout-Anpassungen. Bisher sind die Sprachschriften und
  bei spanischem Rot das Versionsband enthalten. Weitere Grafiken bleiben US.
- GB/GBC: Systemdialoge mit speziell zusammengesetzten Laufzeitvariablen,
  Tausch-/Geschenk-Spitznamen und Sonderereignisse benötigen weitere Szenentests.
- Die drei bereits im deutschen FRLG-Referenzprofil fehlenden US-Textschlüssel
  bleiben auch in den vier neuen GBA-Profilen als US-Rückfall erhalten.
- Vollständige Spielverläufe, alle Kämpfe, Link-Funktionen und Windows/Linux
  wurden nicht praktisch geprüft. Hot-Reload zwischen Sprachmods ist nicht
  Teil der Freigabe; für einen Sprachwechsel die Engine neu starten.
- Die PT-BR-Arbeit muss anschließend gezielt mit dieser Branch zusammengeführt
  und gemeinsam geprüft werden. Diese Preview enthält den stabilen Stand plus
  die hier genannten europäischen Profile.

## Welche Sprach-ROMs fehlen noch?

Für die restlichen französischen, italienischen und spanischen Editionen
fehlen 17 Dateien und anschließend deren jeweilige Profile:

| Sprache | Editionen |
|---|---|
| Französisch | Rot, Blau, Gelb, Kristall, Feuerrot, Rubin, Saphir |
| Italienisch | Rot, Blau, Gelb, Silber, Blattgrün, Rubin, Saphir |
| Spanisch | Blau, Rubin, Saphir |

Hinzu kommen elf japanische Editionen, koreanisches Gold/Silber und optional
japanisches Grün mit eigener Editionszuordnung. Japanisch und Koreanisch
benötigen zusätzliche Zeichensatz- und Layout-Arbeit. Chinesische Fanpatches
und Portugiesisch brauchen eigene definierte Quellen; sie sind keine regulären
Handelsfassungen dieser Liste. Die exakten Dateinamen, Revisionen und Prüfsummen
stehen in Weitere-Sprachen.html.
Für die bestehenden deutschen Profile fehlen weiterhin die passende eigene
Feuerrot-ROM und ein korrekter Saphir-1.1-Dump aus der bisherigen Bestandsprüfung.

## Lizenz

GPLv3 und die bestehenden Drittanbieterbedingungen bleiben erhalten.
Ein Kopier- oder Forkverbot kann diesem GPL-Paket nicht wirksam hinzugefügt
werden. LICENSE-POLICY.md erklärt die Grenzen und die Projektkennzeichnung.

## Prüfumfang

Ergebnis vom 17.10.2026: 13/13 neue Profile bestehen die unten genannten
Szenentests; fünf Unit-/Katalogprüfungen bestehen ebenfalls. Siehe EUROPE-QA.json.

Der isolierte macOS-Test verwendet ausschließlich private ROM-Imports und
separate QA-Spielstände. Für jedes der 13 neuen Profile werden Aktivierung und
Sprache geprüft. GB/GBC zeigen Titel, Stadt, Pokémon-Center, Markt und einen
wirklichen Kartendialog; Gen2 zusätzlich den metrischen Pokédex. Dabei werden
Pokémon- und Attacken-Kampfwerte mit der US-Basis verglichen. FRLG prüft
Feldansichten, Pokémon-Zusammenfassung, unveränderte Basiswerte und Speichern.
Die Ergebnisliste wird im Entwicklungsverzeichnis unter
build/european-live-results.json abgelegt. Die Preview enthält keine ROMs,
Spielstände oder extrahierten ROM-Grafiken.
