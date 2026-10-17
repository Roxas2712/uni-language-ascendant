# Uni-Language Ascendant 1.5.1

Eine eigenständige Mod für Gen1Recomp. Sie liest lokalisierte Texte und Grafiken aus deiner
eigenen Sprach-ROM und legt sie über ein bereits importiertes US-Basisspiel.
Es ist kein spezieller Recompiler-Build erforderlich.

**PT-BR für alle elf Editionen:** Rot, Blau, Gelb, Gold, Silber, Kristall,
Rubin, Saphir, Emerald, Feuerrot und Blattgrün haben eigene Importprofile.
Attackennamen, Status-/Menütexte und Grafikbeschriftungen werden lokalisiert.
Gen3 ergänzt auch Itemnamen, Trainerklassen, Ortsnamen und native Nebenmenüs.
Die Mod ergänzt die importierten Fanübersetzungen durch eigene Korrekturen.
Der aktuelle Prüfstatus mit echten Spielszenen steht in [PT-BR.html](PT-BR.html).
Das ist keine Aussage über einen vollständigen Story-Durchlauf jeder Edition.

Die benötigten Basis- und Sprach-ROMs müssen exakt der [ROM-Liste](ROM-Liste.html)
entsprechen. Saphir verwendet sein eigenes US-Spiel mit der Rubin-PT-BR-Quelle
und gesonderten Saphir-Ergänzungen. Feuerrot/Blattgrün benötigen zum Erstellen
der Sprach-ROM eine andere Basisrevision als zum Starten im Recompiler:
Fanpatch-Basis 1.1, US-Laufzeitbasis 1.0.

Korrektur zur früheren Doku: „Missão concluída! Poções, saúde e proteção.“ war
ein künstlicher Schrift-Test, kein Joy-Dialog. Die aktuelle Doku verwendet echte
NPC-Interaktion samt KP-Erholung und Rückkehr zur Feldsteuerung als Beleg.

Neu in 1.4.2: Die Spielsprachwahl und die Mod-Optionen zeigen pro Edition nur
Sprachen mit einem unterstützten, bereits importierten ROM-Profil. Fehlt eine
zuvor gewählte Sprach-ROM, startet die Mod auf Englisch. Die zehn Menüsprachen
und die Liste der benötigten ROMs bleiben unabhängig davon verfügbar.
Emerald unterstützt zusätzlich Französisch, Italienisch und Spanisch. Die unten
genannten Testgrenzen und verbleibenden US-Textschlüssel gelten ausdrücklich.

## Installation

1. Das passende US-Basisspiel in Gen1Recomp importieren.
2. `uni-language-ascendant-1.5.1.zip` über den Mod-Manager installieren.
3. Bei **Uni-Language Ascendant** die Imports öffnen und die passende
   Sprach-ROM auswählen. Nur die gewünschte Edition ist nötig; die anderen
   Dateien dürfen fehlen.
4. Die Mod für diese Edition aktivieren und das Spiel starten. Vor dem Titelbild
   erscheint die Sprachwahl mit den benötigten ROM-Versionen und SHA-1-Prüfsummen.
5. Beim ersten Start die Menüsprache wählen, anschließend die Spielsprache wählen (mit allen passenden Imports: Emerald EN/DE/FR/IT/ES/PT-BR, übrige Editionen EN/DE/PT-BR). Bei einem Sprachwechsel startet die Engine neu;
   anschließend die Edition im Launcher erneut starten. Die Auswahl wird pro
   Edition gespeichert. Ohne vorherige Auswahl startet die Mod im englischen Modus.

| US-Basisspiel | Zusätzliche deutsche ROM |
| --- | --- |
| Red | Rote Edition |
| Blue | Blaue Edition |
| Yellow | Gelbe Edition |
| Gold | Goldene Edition |
| Silver | Silberne Edition |
| Crystal | Kristall-Edition |
| FireRed **1.0** | Feuerrote Edition **1.0** |
| LeafGreen **1.0** | Blattgrüne Edition **1.0** |
| Ruby **1.0** | Rubin-Edition **1.0** |
| Sapphire **1.0** | Saphir-Edition **1.1 / Revision 1** |
| Emerald **1.0** | Smaragd-Edition **1.0** |

Die Dateien werden anhand ihrer Prüfsumme erkannt. Falsche Editionen und
unbekannte deutsche Revisionen werden abgelehnt. Ohne passende deutsche Datei
bleibt das Basisspiel unverändert; im Log steht, welche Quelle fehlt.

Die Sprachwahl wird bei jedem normalen Spielstart angezeigt. Im Mod-Manager
lässt sich die Sprache ebenfalls vorgeben oder der Auswahlbildschirm ausblenden.
Ein Wechsel mitten im laufenden Spiel wird erst nach einem Neustart wirksam. Andere Sprachmods sollten für
dieselbe Edition deaktiviert sein.

## Umfang

- Deutsche Dialoge und ROM-basierte Menü- und Kampftexte, einschließlich
  Spielerplatzhaltern, Steuerzeichen und Brailleschrift.
- Deutsche Pokémon-, Attacken-, Item- und Trainernamen.
- Deutsche Item-, Attacken- und Fähigkeitsbeschreibungen, Fähigkeitsnamen,
  Trainerklassen, Ortsnamen und Pokédex-Einträge.
- Deutsche Titelgrafiken, Schriften, Typensymbole, Status-, Beutel-, Team-, PC-
  und Trainerkarten-Oberflächen sowie Abspann-Daten.
- Deutsche Namenseingabe bei Rubin, Saphir und Smaragd und angepasste Positionen für
  die größeren deutschen Titelbanner von Rubin und Saphir.
- Welt-Tilesets aus der Sprach-ROM, einschließlich POKé-, MRKT- und Arena-Schildern.
  Die Basis-Karten und Metatile-IDs bleiben erhalten.
- Umlaute und ß werden beim Import korrekt gelesen.
- Die Original-ROMs und der Import-Cache des Basisspiels werden nicht verändert.

Vom Recompiler selbst hinzugefügte Launcher-, Debug- und Online-Oberflächen
gehören nicht zu den ROM-Sprachdaten und können Englisch bleiben. Englische
Pluralfragmente und einzelne ausschließlich englische Abspann-Namen haben
keinen deutschen Gegenpart; der deutsche Abspann stammt aus seinem eigenen
Datenpaket. Alle elf Editionen von Gen1 bis Gen3 sind als Profile enthalten.
Das bedeutet nicht, dass jeder zusätzliche Engine-Text übersetzt oder jedes
Ereignis eines vollständigen Spieldurchlaufs geprüft wurde.

Die Mod braucht die Mod-Schnittstelle mit `mod.imports` und `mod.cache`. Geprüft wurde
Bryans Entwicklungsstand `1925fa9f97661f1e2d0922f7c6eb9546d262fd29` vom
15.10.2026 für diese Version. Die grafischen Tests liefen auf
macOS mit dem separaten Metal-Konfigurationsfix; dieser Fix ist kein Bestandteil
der Mod. Windows/Linux wurden nicht praktisch getestet.

## Technischer Aufbau

Die ZIP enthält Mod-Code, Adressprofile, eigene Übersetzungsergänzungen, Menü-Assets
und die Dokumentation mit Prüfaufnahmen. Lokalisierte ROM-Texte und Spielgrafiken
werden beim ersten Spielstart aus der importierten Sprach-ROM gelesen. ROMs,
Fanpatches, importierte Sprachcaches und Spielstände werden nicht mitgeliefert.

Die Mod verwendet die offiziellen Inhaltsregister für Text- und Namensänderungen.
Private Import-Routinen erzeugen die Sprach- und Grafikdaten. Das Ergebnis wird
in `mod_cache/german_rom_source/compiled/` lokal gespeichert und bei weiteren
Starts wiederverwendet. ROM-Profil, Compiler-Code und relevante Basisdaten bilden
den Cache-Schlüssel. Jeder gespeicherte Inhalt wird vor dem Anwenden geprüft;
unvollständige oder beschädigte Daten werden neu aufgebaut. Der Cache enthält
extrahierte Spielinhalte und gehört nicht in ein verteilbares Mod-Paket.
Ein an den Mod-Lebenszyklus gebundener Leseadapter versorgt damit die verschiedenen
Gen1-, Gen2- und Gen3-Renderer. `engine_internals` wird für diesen Adapter und die Dekodierung benötigt. Die
fehlenden deutschen Zeichen im Decoder werden nur während der synchronen
Extraktion ergänzt und danach wiederhergestellt. Die aktiven Engine-Adressprofile bleiben unverändert. Der Recompiler führt
weiterhin das US-Basisspiel mit dessen Spielregeln aus.

Beim Update die vorhandene Version im Mod-Manager ersetzen; die Mod-ID bleibt
gleich. Individuelle Spitznamen in vorhandenen Spielständen bleiben erhalten.

## Weitere Sprachen

Der Compiler ist profilbasiert. `catalog.lua` verknüpft Edition, Sprache,
Headerkennung und Revision mit Text-, Grafik- und Weltprofilen sowie Zeichensatz.
Eine validierte Prüfsumme wählt das passende Profil; der Dateiname ist unerheblich.
Mehrere Sprachen können gleichzeitig importiert sein; beim Start wird eine ausgewählt.

**Enthalten: Deutsch und PT-BR für alle elf Editionen, zusätzlich Französisch,
Italienisch und Spanisch für Emerald (Revision 0).** Englisch stammt aus dem US-Basisspiel.
Die drei neuen Profile wurden mit den bereitgestellten ROMs importiert und in
Live-Szenen geprüft: Titel, Center, Markt, Dialog, Pokémon-Bericht und Speichern.
Die Namenseingabe berücksichtigt acht Spalten in IT/ES und neun in FR/DE.
Akzente und lokalisierte zusammengesetzte Fontzeichen werden dekodiert.

Das ist keine vollständige Durchspielprüfung. In Version 1.4.1 sind je Sprache
15.653 von 15.655 registrierten Textschlüsseln zugeordnet. Die zuvor fehlenden
42 französischen, 54 italienischen und 49 spanischen Schlüssel sind ergänzt.
Zusätzlich wurden vertauschte Dialogzuordnungen korrigiert. Die beiden übrigen
Schlüssel betreffen ausschließlich englische Abspann-Namen:
`sCreditsText_NicolaPrattBarlow` und
`sCreditsText_RoyalNewZealandFederationBlind`; diese bleiben unverändert.

Die eventbasierten Textverweise werden anhand dekodierter Skriptbefehle geprüft.
Nur Muster, die in Quell- und Ziel-ROM eindeutig sind, dienen als Startpunkte;
weitere Verweise werden über passende Skriptoperanden verfolgt. Textblockränder
werden an beiden Enden geprüft, die Spielerzahltexte über ihre Pointertabelle.
Japanische Resttexte in den europäischen ROMs sind damit nicht als japanische
Spielsprachunterstützung freigegeben. Ein unabhängiger vollständiger Import-
oder Durchspielvergleich aller FR/IT/ES-Inhalte ist weiterhin nicht erfolgt.

Japanisch, Koreanisch und FR/IT/ES für andere Editionen bleiben Entwicklungsbedarf.
Ein beliebiges ROM lässt sich nicht allein durch Spracherkennung sicher auf
US-Adressen abbilden. Japanisch benötigt einen eigenen Decoder, Schriftensatz
und gegebenenfalls Layoutanpassungen.

Für weitere Sprachen: exakt passende Symbol-/Adressdaten und Zeichensatz
bereitstellen, `profiles/` ergänzen, den Katalog sowie `optional_imports` mit
ROM-Prüfsumme erweitern und Texte, Grafikdaten und Live-Szenen gegen einen
unabhängigen Import prüfen. Der Compiler und sein persistenter Cache werden
unverändert wiederverwendet. `tools/export_world.lua` erfasst dazu die Weltprofile;
`tools/join_world.lua` ordnet die sprachabhängigen Paare den US-Karten zu.
Die Entwicklungswerkzeuge erzeugen die registrierten Adressprofile;
sie sind kein automatischer Profilgenerator für unbekannte ROMs.

## Credits

Based on the Pokemon Gen 1 Recompilation Project by BOIS CLUB GAMES, LLC
(https://github.com/bryanthaboi/gen1recomp)

Adressmetadaten wurden aus den vorhandenen Gen1Recomp-Importprofilen und den
zu den ROM-Versionen passenden Symboltabellen abgeleitet. Dazu gehören die
pret-basierten LeafGreen-Symbole, die deutschen Ruby-Symbole aus
https://github.com/Kakumi/Pokebot und die rebasierten deutschen Emerald-Symbole
aus dem lokalen Importprototyp. `LICENSE.MD` enthält die Lizenzbedingungen des
zugrunde liegenden Projekts.

`VENDOR.md` dokumentiert die eingebundenen Import-Routinen.

## Gen1 und Gen2 in Version 1.4.0

Die sechs zusätzlichen Profile lesen ihre Texte über geprüfte Adressspannen
und erzeugen Schrift, Titel, Menügrafiken und die lokalisierten Außen-Tilesets
aus der deutschen ROM. Gen2-LZ3-Grafiken werden dabei einmal dekomprimiert.
Paletten und Kachelanordnung sind Profil-Metadaten. Die ZIP enthält weder die
Bilder noch die dekodierten Dialoge. Symbolische US-Schlüssel ordnen die
Ergebnisse dem Basisspiel zu; Platzhalter und Textbox-Steuerung bleiben erhalten.

Der lokale Vergleich erfasst 2.582 Dialogeinträge je Rot/Blau, 2.695 für Gelb,
3.044 je Gold/Silber und 3.991 für Kristall (einschließlich leerer Referenzslots).
Alle Dialogeinträge dieser zugeordneten Referenz sind rekonstruierbar. Das ist
kein Nachweis, dass jede denkbare Laufzeitsituation oder jeder Engine-Zusatz
übersetzt ist. Nicht aus der ROM ableitbare Zusatztexte und dynamische
Engine-Formulierungen können weiterhin Englisch erscheinen.

Namen, Beschreibungen und Texte wurden mit der lokalen Referenz verglichen;
Spielwerte und Attackeneffekte bleiben auf den US-Daten. Kalter Erststart,
Cache-Neustart und deaktivierte Mod wurden für alle sechs Editionen geprüft.
Live-Bilder dokumentieren Titel, Center, Markt und ein lesbares Stadtschild.
Alle fünf deutschen Gen3-Profile bleiben enthalten.

Die ältere Universal-Sprachmod dient nur als Entwicklungsreferenz und muss
nicht installiert sein. Ihre nachbearbeitete Gelb-Titelgrafik wird nicht
übernommen; die neue Mod verwendet die Anordnung der deutschen ROM.
Einige alte Referenztexte in Gold/Silber/Kristall wurden gegen die ROM
korrigiert. VM-Bezeichnungen stammen aus der deutschen Darstellung.

Gen1-/Gen2-Profile liegen unter `gb/profiles/`; die zugehörigen Anzeigeadapter
werden in `catalog.lua` ausgewählt. Weitere Sprachprofile benötigen eigene
Prüfsummen, Adressen, Zeichensätze und gegebenenfalls Anzeigeadapter.
Eine unbekannte ROM wird nicht geraten oder automatisch als unterstützt markiert.

## Exakte ROM-Versionen und Erweiterungen

Die vollständige Liste steht in `ROM-Liste.html` und `rom_requirements.lua`.
SHA-1 bezeichnet den gesamten ROM-Inhalt, nicht den Dateinamen. Der Mod-Importer
prüft zusätzlich MD5 und Dateigröße; bei der Erstverarbeitung wird SHA-1 geprüft.
Für alle Profile wird auch die SHA-1 des importierten Basisspiels geprüft.
Die hier geprüften US-Basen sind Revision 0 (1.0). Andere vom Recompiler
unterstützte Revisionen sind damit nicht automatisch für diese Sprachmod freigegeben.

Für weitere Sprachen und Revisionen wird ein neues Profil mit einer eigenen
Import-ID in `catalog.lua` registriert. Die Sprachwahl entsteht aus diesem Katalog;
mehrere Sprachen können parallel importiert sein. GB/GBC-Profile benennen ihren
eigenen Decoder, Laufzeitadapter und gemeinsame Hilfsmodule; GBA-Profile benennen
Text-, Grafik-, Kartenprofile und Zeichensatz. Es gibt keine Heuristik, die
unbekannte Sprach-ROMs mit geratenen Adressen lädt.

`adapters.lua` registriert die Import-Adapter pro Generation. Eine zukünftige
Generation benötigt zusätzlich eine passende Spielengine im Recompiler,
Adressprofile und Tests. Aktuell werden ausschließlich Gen1, Gen2 und Gen3 angeboten.

Feuerrot DE 1.0 und Saphir DE 1.1 wurden mit lokal kompilierten Referenz-ROMs
geprüft, deren SHA-1 den veröffentlichten Referenzen entspricht. Die übrigen
Sprachprofile wurden mit den bereitgestellten ROM-Dateien geprüft. Die vorhandene
Saphir-Datei mit SHA-1 `99f7ad71de5de97ca643f2c4123a77ee79af8e80` ist nicht die
freigegebene Revision: sie weicht in einem Audiobereich vom Referenzdump ab.
Es wird keine ROM mitgeliefert oder vom Installer heruntergeladen.

Messwerte und ihre Grenzen stehen in `Performance.html`. Die Startauswahl
entfernt ihre zusätzlichen Draw-, Update- und Eingabe-Wrapper vollständig,
sobald das Spiel freigegeben wird. ROM-Dekodierung erfolgt nur beim Erzeugen
eines noch fehlenden oder ungültigen Sprach-Caches.

## Menüsprachen und Emerald / Smaragd

Uni-Language Ascendant bietet vollständig übersetzte eigene Auswahlmenüs auf
Deutsch, Englisch, Französisch, Italienisch, Spanisch, Japanisch, Koreanisch,
vereinfachtem und traditionellem Chinesisch. Die Menüsprache wird separat und
über alle Editionen hinweg gespeichert. Mit **L** oder der Sprachschaltfläche
oben rechts öffnest du die Auswahl erneut. Die Engine-eigenen Launcher-Menüs
gehören nicht zu dieser Mod.

Diese neun Menüsprachen sind unabhängig von den aktuell geprüften **EN/DE-Spielprofilen sowie FR/IT/ES für Emerald**.
Die englische Emerald-ROM „USA, Europe“ (BPEE) ist keine mehrsprachige Ausgabe.
Deutsch (BPED) und andere lokalisierte Editionen sind separate ROMs. Interne
Sprachkennungen, zum Beispiel für getauschte Pokémon, enthalten keine kompletten
Sprachpakete. Ein englischer Emerald-Import schaltet deshalb keine weiteren
Spielsprachen frei. Zusätzliche Sprach-ROMs benötigen eigene verifizierte Profile.

Die Schriftdateien sind kleine, mitgelieferte Noto-Sans-CJK-Teilmengen unter SIL OFL 1.1;
Lizenz und Herkunft stehen unter `fonts/`. Neue UI-Texte benötigen gegebenenfalls
eine Aktualisierung dieser Teilmengen.

## Einmaliges Ascendant-Intro (1.4.0)

Beim ersten Mod-Start läuft das originale Ascendant-Intro aus Origami Ascendant
mit Pikachu, Evoli, Mew und Klang. Danach erscheint beim neuen Profil zunächst der englische Hinweis und anschließend die Sprachwahl. Enter,
Leertaste, Escape, Controller A/B/Start oder ein Klick/Tippen überspringen es.
Das Intro wird nach Abschluss oder bewusstem Überspringen editionsübergreifend
als gesehen gespeichert; auch ein Sprachwechsel oder Mod-Update spielt es nicht
erneut ab. Ein Abbruch vor Abschluss oder ein fehlgeschlagener Schreibvorgang
verbraucht den Erststart nicht. Der Status gehört zum Datenverzeichnis der
Installation, nicht zum Spielstand oder einer einzelnen Edition.

Die Einstellung zum Ausblenden der Sprachwahl unterdrückt nicht das einmalige
Intro. Dessen Grafik- und Klangressourcen werden direkt danach freigegeben.
Das Intro übernimmt die vorhandene Stummschaltung (`splashMute`) und Lautstärke.

### Zusätzliche Spielsprachen

**Noch nicht freigegeben:** Japanisch und Koreanisch sowie FR/IT/ES für andere
Editionen als Emerald. `Weitere-Sprachen.html` nennt die noch benötigten ROMs
und SHA-1-Prüfsummen. Die drei gelieferten Emerald-ROMs sind dort entfernt und
stehen jetzt als unterstützte Imports in `ROM-Liste.html`.

## Zurück, Zurücksetzen und Deinstallation

Vor dem Spielstart führen **Zurück / Esc / Controller B** zur vorherigen Auswahl.
Eine nur angezeigte, noch nicht bestätigte Menüsprache wird dabei verworfen.
**Profil zurücksetzen / R / Controller X** öffnet eine Bestätigung mit
„Abbrechen“ als Standard. Erst die Bestätigung löscht die gespeicherten Menü-
und Spielsprachen für alle Editionen, den Intro-Status und den Erststart-Hinweis
und startet die Engine neu. Importierte ROMs und Spielstände bleiben dabei erhalten.

Beim ersten Einrichten steht vor der Sprachauswahl auf Englisch:

> Uninstalling this mod deletes its profile and imported language ROMs. Reinstalling starts fresh. Updates preserve your profile.

Die persönlichen Einstellungen liegen als Datendatei innerhalb der Installation
unter `baseroms/.uni-language-profile`. Der normale Launcher übernimmt dieses
Verzeichnis bei Updates und löscht es bei der Deinstallation. Nach einer echten
Deinstallation/Neuinstallation werden auch zurückgebliebene Launcher-Sprachoptionen
für diese Mod auf die Vorgaben zurückgesetzt. Einstellungen anderer Mods und
Spielstände werden nicht geändert. Der getrennte, generierte Sprach-Cache kann
im Engine-Datenverzeichnis verbleiben; daraus werden keine persönlichen
Einstellungen wiederhergestellt. Diese Version übernimmt die alten 1.3.0-
Präferenzen im Mod-Cache bewusst nicht in das neue Profil.


## Emerald 1.4.0: Startzeit und Speicher

Neun Vergleichsläufe mit jeweils 360 Frames: EN/FR/IT/ES/DE/ES/IT/FR/EN.
FR/IT/ES wurden beim ersten Start in rund 12 Sekunden verarbeitet. Warme
Starts lagen unter der aktuellen Rechnerlast bei etwa 4,5–5,1 Sekunden;
DE bei 9,2 Sekunden. Alle nichtenglischen Messläufe trafen den Cache.
Die Draw-Mediane lagen zwischen 13,4 und 14,0 ms. Das ist kein Nachweis
identischer Performance: Andere Aufgaben liefen gleichzeitig.
Der beobachtete Lua-Heap war mit Sprachdaten größer (196–202 MiB gegenüber
rund 96 MiB bei EN, ohne erzwungene GC). Details und ältere Messreihen stehen
in `Performance.html`.

Bei mehr als drei Spielsprachen bieten die Pfeile neben der Sprachwahl
auch per Maus Zugriff auf die weiteren Sprachen. Links/Rechts auf Tastatur
und Controller wechseln weiterhin durch alle Einträge.


## Version 1.5.1: Sprachcache und Speicher

Der Sprachcache verwendet jetzt ein begrenztes binäres Datenformat. Geladene
Cache-Dateien werden nicht als Lua-Code ausgeführt. Bereits vollständig ersetzte
Übersetzungseinträge werden nicht länger zusätzlich gespeichert; der endgültige
Text und seine Steuerzeichen bleiben erhalten. Große Gen3-Rohgrafiken bleiben verlustfrei
komprimiert im Speicher, bis das Spiel sie zum ersten Mal benötigt. Anschließend
wird das entpackte Ergebnis wiederverwendet. Bereits komprimierte PNGs und
Lua-Manifeste bleiben direkt verfügbar. Ein vollständiger Zugriff auf die
exportierte Asset-Tabelle entpackt weiterhin alle Einträge für andere Mods und
Diagnosewerkzeuge.

Beim ersten Start nach dem Update wird der Sprachcache einmal neu aufgebaut.
Das ist ein kalter Start und nicht mit einem späteren Warmstart vergleichbar.
ROM-Imports, gewählte Sprachen, Intro-Status und Spielstände bleiben erhalten.
Beschädigte Cache-Dateien lösen einen vollständigen Neuaufbau aus.

Die aktuellen Vorher-/Nachher-Messungen und Spielbilder stehen in
[PT-BR.html](PT-BR.html). Speicherwerte hängen davon ab, welche Bildschirme bereits
geöffnet wurden; es gibt keine feste Obergrenze für die Ersparnis. Der bisherige
Bericht in `Performance.html` dokumentiert ältere Versionen.
