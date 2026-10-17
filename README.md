# Uni-Language Ascendant

A standalone language mod for **Gen1Recomp**. Import the exact English base game,
then your own supported language ROM. The mod compiles localized text and graphics
once and reuses its local cache on later launches.

Based on the Pokemon Gen 1 Recompilation Project by BOIS CLUB GAMES, LLC
(https://github.com/bryanthaboi/gen1recomp).

## Brazilian Portuguese for Gen1–Gen3

Version 1.5.0 contains PT-BR profiles for all eleven editions: Red,
Blue, Yellow, Gold, Silver, Crystal, Ruby, Sapphire, Emerald, FireRed and LeafGreen.
It combines exact fan-translation ROM imports with authored corrections, move
names and native UI/graphic localization. See the generated
[gameplay report](mod/PT-BR.html) and [machine-readable QA](docs/PT-BR-QA.json)
for the current verification status. A profile being enabled is not a claim that
every story or multiplayer branch has been played.

The source ROM and revision must match [the ROM checklist](mod/ROM-Liste.html).
[Source projects and patch identities](tools/ptbr_sources.json) are recorded
separately. FireRed/LeafGreen fanpatches use a 1.1 patch base, while their
recompiler runtime uses the supported US 1.0 base. Do not interchange them.
Sapphire uses its own US game, exact-source reuse from the Ruby PT-BR import,
and separate Sapphire translations, including its Pokédex entries.

All 165/251/354 move IDs retain their gameplay identity and receive Portuguese
display names. Gen3 also covers abilities, item names and descriptions, trainer classes,
map labels, Easy Chat vocabulary, PokéNav and native side-menu text; FireRed/LeafGreen include Help and Fame Checker.
Saved Easy Chat word IDs and unlock rules are preserved. Raster lettering is
compiled into the language cache; the mod does not translate images each frame.

**Evidence correction:** “Missão concluída! Poções, saúde e proteção.” was a
synthetic font fixture, not Nurse Joy's dialogue. It is excluded from the report.
Current healing evidence is reached through actual NPC interaction and checks
HP restoration and returned field control. Other fixtures prepare saves, maps,
party members or inventory; they never supply display dialogue. Unit tests are
reported separately from gameplay evidence.

The menu has ten languages, including PT-BR. Menu and game language can be
selected independently. Back and Reset remain available. The intro runs once
per mod profile; updates preserve that profile, uninstalling deletes it, and
reinstallation starts fresh. The first-run notice explains this in English.

Build with `python3 tools/package.py`. No ROM or fanpatch is included.

## Install version 1.5.0

1. Download [uni-language-ascendant-1.5.0.zip](https://github.com/Roxas2712/uni-language-ascendant/releases/tag/v1.5.0).
2. Import the matching US base ROM in Gen1Recomp.
3. Install the ZIP through the mod manager, enable the mod for your game, and
   import your language ROM under **Uni-Language Ascendant → Imports**.
4. Launch the game, choose your menu language, then your game language.

The game picker and mod options show only supported languages with an imported
ROM for the current edition. English is always available. Menu languages and the
ROM requirements list remain available independently. If a previously selected
ROM is missing, the mod starts in English.

**Updating preserves your mod profile. Uninstalling deletes it; reinstalling
starts fresh.** The first-run Ascendant intro, Back navigation and Reset profile
are included. Changing game language requires a restart.

## Supported profiles

| Games | Game languages |
| --- | --- |
| Red, Blue, Yellow | English base + German, Brazilian Portuguese |
| Gold, Silver, Crystal | English base + German, Brazilian Portuguese |
| FireRed, LeafGreen, Ruby, Sapphire | English base + German, Brazilian Portuguese |
| Emerald | English base + German, French, Italian, Spanish, Brazilian Portuguese |

Menu languages: English, German, French, Italian, Spanish, Japanese, Korean,
Simplified Chinese, Traditional Chinese and Brazilian Portuguese. A translated menu does not imply a
game-language profile exists.

Exact versions and SHA-1 checksums are in [the ROM catalog](tools/rom_requirements.json)
and the bundled [ROM-Liste.html](mod/ROM-Liste.html). Sapphire requires the listed
German revision 1.1 with the English 1.0 base; other revisions are not interchangeable.
No ROMs, decoded game data, saves, personal profiles or compilation caches are
included. The Ascendant intro assets and menu fonts are distributed with their
source and attribution notices.

## Verification and limitations

The version 1.5.0 report records the current gameplay checks, exact runtime and
test-helper fingerprints, screenshot hashes and paired English/PT-BR performance
runs for every edition. The report builder refuses final output when a required
run is missing, stale, failed or only a focused sample. See
[PT-BR.html](mod/PT-BR.html) and [PT-BR-QA.json](docs/PT-BR-QA.json).

The release passes 58 functional groups, 44 paired performance runs, 69 Python
unit tests and nine Lua unit groups. All 22 PT-BR measurements hit the language
cache. On the tested M3 Mac, Emerald's median observed rate was 59.84 FPS in both
languages, while its cached PT-BR mod load took 3.79 seconds and its measured Lua
heap was 211.8 MiB versus 96.1 MiB in English. These are stationary overworld
measurements under VSync and background load, not a universal performance guarantee
or process-RAM figures. The report includes every edition and all raw measurements.

Earlier version 1.4.2 passed unit checks for game/import filtering, fallback selection,
all nine menu locales, preferences and intro lifecycle. Live Emerald runs checked
English-only and English/Spanish imports, fallback from an absent French import,
and the five-language picker including mouse paging and a French in-game dialogue.
ZIP install, update, uninstall and reinstall were tested separately.

The 1.4.1 Emerald FR/IT/ES text correction checks cover 176 added or changed keys
across cold and warm loads. Each profile maps 15,653 of 15,655 text keys; two
English-only credits keys remain. This is not a full-playthrough certification.
See [the detailed mod documentation](mod/README.md) and
[performance measurements](mod/Performance.html) for earlier coverage and limits.

Tested against upstream commit `1925fa9f97661f1e2d0922f7c6eb9546d262fd29`, on macOS
with the separate Metal configuration fix. Windows and Linux have not been
practically tested. The mod does not include an engine build or the Metal fix.

## Development

- `mod/`: complete distributable runtime, address profiles, intro, fonts and docs.
- `tools/`: packaging, catalog generation and profile development tools.
- `tests/`: unit checks and live drivers for an isolated upstream engine.
- `compatibility/`: pinned upstream and ROM identity metadata.

Build the installable archive with Python 3:

```sh
python3 tools/package.py
```

The packager uses an explicit runtime allowlist and rejects ROM/save files in
the archive. Build products go into ignored `dist/`; installable ZIPs and their
SHA-256 checksums are published as release assets.

Run the independent startup/preferences/intro tests with LuaJIT:

```sh
luajit tests/startup_unit.lua "$PWD"
luajit tests/preferences_unit.lua "$PWD"
luajit tests/intro_unit.lua "$PWD"
```

The remaining tests require the pinned engine under `build/upstream-engine`,
LÖVE, private ROM inputs and dedicated QA save identities. Set `LOVE` to your
LÖVE executable, `LUAJIT` to LuaJIT and `ULA_GB_REFERENCE` to the private Gen1/Gen2
reference directory where applicable. These private inputs are deliberately not
part of this repository. Some profile-generation scripts consume intermediate
files under `build/`; they are development tools, not a one-command universal
ROM importer. The existing address profiles are sufficient to build the mod ZIP.

New languages require verified text/graphics profiles and catalog entries.
New generations also require an appropriate engine and runtime adapter.

## Attribution

See [LICENSE.MD](LICENSE.MD) and [VENDOR.md](mod/VENDOR.md) for upstream code,
the German Universal reference, Noto fonts and the shared Origami Ascendant intro.


### Reproduce PT-BR QA

Use a stock engine checkout and an isolated copy of an already imported US
Emerald cache. The runner uses an isolated `german-rom-mod-ptbr-*` QA identity, never the player’s
normal save identity. Substitute your own absolute paths:

```sh
python3 tests/run_ptbr.py --engine /path/to/gen1recomp --love /path/to/love --base-cache /path/to/emerald --rom /path/to/emerald-ptbr.gba --mode live
python3 tests/run_ptbr.py --engine /path/to/gen1recomp --love /path/to/love --mode menu
python3 tests/run_ptbr.py --engine /path/to/gen1recomp --love /path/to/love --mode performance
python3 -m unittest discover -s tests -p 'test_*.py'
```

`tools/apply_bps.py BASE PATCH OUTPUT` validates source, patch and target CRCs
and refuses to overwrite an existing output file. The profile builder separately
pins the source and target SHA-1 values. `tools/export_asset_metadata.lua` records
metadata using the shipped private extractors without altering engine/vendor
files; `tools/build_emerald_ptbr.py --help` lists its private inputs.
