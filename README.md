# Uni-Language Ascendant

A standalone language mod for **Gen1Recomp**. Import the exact English base game,
then your own supported language ROM. The mod compiles localized text and graphics
once and reuses its local cache on later launches.

Based on the Pokemon Gen 1 Recompilation Project by BOIS CLUB GAMES, LLC
(https://github.com/bryanthaboi/gen1recomp).

## PT-BR development preview

The `feature/pt-br` branch adds a Brazilian Portuguese menu and an Emerald
import profile for **Zambrakas 2013-12-08, without the day/night patch**.
The matching BPS patch is linked in [the in-game QA document](mod/PT-BR.html).
Apply it to your own US Emerald dump, then import the patched ROM:

- US base SHA-1: `f3ae088181bf583e55daf962a92bb46f4f1d07b7`
- PT-BR source SHA-1: `18a2b0acdba046c71b8677bb58c9ee7d36f7a91f`

All 15,655 text keys are mapped and the profile passes live smoke tests,
including a scripted wild battle through victory and return to the field.
**The source fan translation still contains English text.** This is not a full
playthrough or a complete linguistic review. The picker states that limitation
in all ten menu languages. Menu choice, Back, reset, persistence and all menu
font glyphs were tested.

**Ruby and Sapphire are also development previews; the other eight editions remain hidden.**
Both use the OJ Abreu Ruby PT-BR ROM as their imported translation source
(SHA-1 `90f1464f77c57b4eef45ee07df140d402162eee3`). Sapphire runs its own
US base, retains its own title/world assets, reuses only text with exactly
matching English source IR, and adds 203 authored edition-specific Pokédex
entries (405 pages). All 13,457 text keys are mapped. This is not full linguistic
coverage: English labels and inherited fan-translation defects remain.
Progress is recorded in [ptbr_sources.json](tools/ptbr_sources.json).

**Screenshot correction:** “Missão concluída! Poções, saúde e proteção.” was a
synthetic Ruby font fixture, not Nurse Joy's dialogue. It must not be used as
translation evidence. The misleading Emerald caption was also corrected.
Authored healing dialogue is now tested through actual field interaction,
including HP recovery and return of control. It is pinned to original text IR
hashes and applied to both symbol and address aliases.

Build the installable preview with `python3 tools/package.py`; it writes
`dist/uni-language-ascendant-1.5.0-preview.2.zip`. The latest stable release
remains 1.4.2 below. No ROM or translation patch is included.

## Install version 1.4.2

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

## Supported profiles

| Games | Game languages |
| --- | --- |
| Red, Blue, Yellow | English base + German |
| Gold, Silver, Crystal | English base + German |
| FireRed, LeafGreen, Ruby, Sapphire | English base + German |
| Emerald | English base + German, French, Italian, Spanish; PT-BR in the preview |

Menu languages: English, German, French, Italian, Spanish, Japanese, Korean,
Simplified Chinese, Traditional Chinese and Brazilian Portuguese (preview). A translated menu does not imply a
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
Emerald cache. The runner always uses `german-rom-mod-ptbr-qa`, never the player’s
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
