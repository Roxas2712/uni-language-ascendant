# European expansion preview

13 additional profiles based on v1.4.2. Preview 5 adds a focused editorial pass
and short font/UI/profile regressions; complete playthroughs remain outside
this preview’s validation. Preview 4 completes the known GBA registry
gaps, adds 245 supplemental GBA UI entries per language (DE/ES/FR/IT), and fixes
regional item plurals. It retains Preview 3’s complete AI editorial review of 1,520 supplemental
GB/GBC strings per language, native NPC/gift identities, endgame graphics
and broader gameplay, localhost link and save/restart regression tests. See [EUROPE-PREVIEW.md](EUROPE-PREVIEW.md)
for coverage, QA limits, missing ROMs and PT-BR merge status, and
[LICENSE-POLICY.md](LICENSE-POLICY.md) for the existing GPL obligations.

# Uni-Language Ascendant

A standalone language mod for **Gen1Recomp**. Import the exact English base game,
then your own supported language ROM. The mod compiles localized text and graphics
once and reuses its local cache on later launches.

Based on the Pokemon Gen 1 Recompilation Project by BOIS CLUB GAMES, LLC
(https://github.com/bryanthaboi/gen1recomp).

## Install the stable release 1.4.2

1. Download [uni-language-ascendant-1.4.2.zip](https://github.com/Roxas2712/uni-language-ascendant/releases/tag/v1.4.2).
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

For this branch, build the preview with `python3 tools/package.py` and install
the resulting `dist/uni-language-ascendant-1.4.3-europe-preview.5.zip` through
the same mod manager. PT-BR development remains separate.

## Supported profiles in this preview

| Games | Game languages |
| --- | --- |
| Red, Yellow | English base + German, Spanish |
| Blue | English base + German |
| Gold | English base + German, French, Italian, Spanish |
| Silver | English base + German, French, Spanish |
| Crystal | English base + German, Italian, Spanish |
| FireRed | English base + German, Italian, Spanish |
| LeafGreen | English base + German, French, Spanish |
| Ruby, Sapphire | English base + German |
| Emerald | English base + German, French, Italian, Spanish |

Menu languages: English, German, French, Italian, Spanish, Japanese, Korean,
Simplified Chinese and Traditional Chinese. A translated menu does not imply a
game-language profile exists.

Exact versions and SHA-1 checksums are in [the ROM catalog](tools/rom_requirements.json)
and the bundled [ROM-Liste.html](mod/ROM-Liste.html). Sapphire requires the listed
German revision 1.1 with the English 1.0 base; other revisions are not interchangeable.
No ROMs, decoded game data, saves, personal profiles or compilation caches are
included. The Ascendant intro assets and menu fonts are distributed with their
source and attribution notices.

## Verification and limitations

Version 1.4.2 passed unit checks for game/import filtering, fallback selection,
all nine menu locales, preferences and intro lifecycle. Live Emerald runs checked
English-only and English/Spanish imports, fallback from an absent French import,
and the five-language picker including mouse paging and a French in-game dialogue.
ZIP install, update, uninstall and reinstall were tested separately.

The 1.4.1 Emerald FR/IT/ES text correction checks cover 176 added or changed keys
across cold and warm loads. Each profile maps 15,653 of 15,655 text keys; two
credit identities are now explicitly preserved as proper names in Preview 4. This is not a full-playthrough certification.
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


The European preview matrix is reproducible with private ROM imports and an
isolated `ula-europe-expansion-qa` identity:

```sh
LOVE=/path/to/love LUAJIT=/path/to/luajit python3 tests/run_european_release.py
```

It includes all 13 scene profiles, nine GB/GBC menu/catalog/gameplay/localhost
link profiles, ten English/disabled process restarts, and six unit/catalog checks.
The complete source-key audit is `tools/audit_european_ui.py`. The authoritative
reviewed ES/FR/IT layer is `translations/european/gb-ui-overrides.tsv`; regenerate
with `tools/build_european_ui.py` then `tools/sync_european_ui.py`. Native ROM
names are generated by `tools/build_european_gifts.py`; private evidence remains
under ignored `build/`. The matrix is targeted integration coverage, not a full
playthrough or native-speaker certification.
