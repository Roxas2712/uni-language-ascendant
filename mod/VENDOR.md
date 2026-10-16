# Eingebundener Quellcode

`vendor/src/` enthält Import- und Text-Routinen aus Gen1Recomp von
BOIS CLUB GAMES, LLC, Quellstand `1925fa9f97661f1e2d0922f7c6eb9546d262fd29`.
Die Dateien unterliegen den Bedingungen in `LICENSE.MD`. Sie werden als private
Mod-Module geladen; es werden keine installierten Engine-Dateien ersetzt.

Fünf Routinen enthalten die bereits im lokalen deutschen Importprototyp
verwendeten Anpassungen:

- `rs/extract_common_ui.lua`: bekannte Cursorlänge trotz größerer Symbolspanne.
- `rs/extract_pokedex_detail.lua`: deutschen Cry-Meter-Tilemap-Ausschnitt wählen.
- `rs/extract_credits.lua`: editionsabhängige Anzahl der Abspannseiten und
  Palettenfarbe der Überschriften.
- `rse/credits_extract.lua`: eigene deutsche Schlussbild-Tilemap verwenden.
- `rse/extract_naming_rse.lua`: Tastaturzeilen und Spalten aus den ROM-Tabellen
  bestimmen.

Die Profile enthalten ausschließlich Adressen, Größen, symbolische Bezeichner
und Formatparameter. `tools/export_assets.lua` im Entwicklungsprojekt zeichnet
die benötigten Metadaten während einer Extraktion der überprüften ROMs auf.

`tileset.lua`, `metatile.lua` und `native_pack.lua` erzeugen zusätzlich die
Welt-Atlanten. Die Profile enthalten hierfür nur Adressen und Paarzuordnungen,
keine Grafikdaten.


Die Anzeigeadapter unter `gb/runtime/`, `gb/adapters/` und die Hilfsfunktionen
unter `gb/shared/` basieren auf der vom Nutzer bereitgestellten lokalen
Translation German Universal 0.2.0 (Roxas2712). Die früheren extrahierten
Sprachkataloge und PNG-Dateien werden nicht verteilt. Die neue Kompilation
rekonstruiert diese Inhalte aus der privaten ROM anhand der Adressrezepte.
Metrische Pokédex-Maße sind separate numerische Anzeigemetadaten; insbesondere
bleiben die US-Gewichte für Gen2-Kampfmechanik erhalten.

Die Gelb-Titelanordnung wurde zusätzlich mit dem zu dieser ROM passenden
Disassembly https://github.com/Brianum/pokeyellow-de abgeglichen. Das Paket
enthält daraus keine Bilder oder ROM-Daten.

Die Menüs verwenden umbenannte Glyphen-Teilmengen von Noto Sans CJK Regular
unter SIL OFL 1.1. Herkunft: https://github.com/notofonts/noto-cjk .
Lizenz und Copyright stehen in `fonts/OFL.txt`; `fonts/SOURCE.txt` beschreibt
die Änderung. Diese Schriftlizenz gilt unabhängig von der Mod-Quellcodelizenz.

Das einmalige Intro unter `intro/` wurde unverändert aus dem vom Nutzer
bereitgestellten Origami Ascendant übernommen (Origami-Innenraeume,
`gen3/integrated/ascendant_startup`). Die fünf Bild-/Klangdateien stimmen mit
dessen `ASSET-SHA256.json` überein. Herkunftshinweise stehen in `intro/SOURCE.txt`.
Die neue Ablaufsteuerung und editionsübergreifende Erststartmarkierung liegen
in `intro.lua` und `startup.lua`.

## Emerald FR / IT / ES (1.4.0)

The new profiles contain address metadata only. Developer tools in
`tools/*emerald_languages.py` derive relocation candidates from the existing
DE symbols, normalize ARM/Thumb code and pointer structures, and validate
indexed tables against the exact user-provided revision-0 ROMs. Pokédex
text addresses use national dex indices; keyboard widths and compressed
palette headers are explicitly checked. Unresolved text keys retain the US
registry entry. This is not an independent full decompilation comparison.

`latin_glyphs.lua` extends the synchronous text decoder with the Latin font
indices already represented by upstream `FrlgFont.LATIN_GLYPHS`, plus localized
ordinal/PC/Pokémelle font cells. Decoder changes are restored after extraction.
No source ROM, ROM excerpt, decoded game text, or game screenshot is packaged.

### Text corrections in 1.4.1

`script_emerald_texts.py` decodes pointer operands using the upstream Emerald
opcode schema instead of treating arbitrary 0x08 bytes as pointer boundaries.
Seed patterns must be unique in both ROMs; matching control-flow references
propagate the mapping. `boundary_emerald_texts.py` verifies text runs against
both adjacent script/data boundaries. `players_emerald_texts.py` validates the
four indexed dynamic player-count strings. The audit JSON remains development
material, outside the distributed archive. Live tests compare every added or
changed registry key to decoded bytes from the exact input ROM on cold/warm load.
