# Asian Gen2 profile build and verification

These profiles have complete extracted text-slot coverage. Scenario QA and
native-ROM versus authored provenance are documented in `../mod/ASIAN-PREVIEW.md`
and `../mod/ASIAN-QA.json`. This is not overall merged-release approval; the
normal package gate remains in force.

## Local inputs

The builders require the three exact ROM SHA-1 identities recorded in the
profiles. They write address recipes; ROMs, extracted text, compiled images and
live screenshots belong in ignored local directories, not Git.

- `build/upstream-engine`: the unmodified engine and its US manifests.
- `../Uni-Language-Ascendant-Europe/build/pokegold`: exact US Gold/Silver ROMs
  and matching `.sym` files.
- `../Uni-Language-Ascendant-Europe/build/pokecrystal`: exact US Crystal ROM,
  matching `.sym`, and `constants/charmap.asm` with the Japanese mapping.
- `build/pokegold-kr`: Narishma-gb/pokegold-kr at
  `c90f31dadef17f033a8f1bdada701b26cef18241`, built with the local Korean
  cartridge inputs. Its Gold/Silver outputs must match the retail hashes before
  their symbols can be used. The builders enforce both native and US hashes.
- `../Pocket Monsters - Crystal Version (Japan).gbc`: exact Japanese cartridge.
- `tools/asian_gen2_refs/*.json`: checked address-only mapping checkpoints.
  Native mappings, bounded inline-ASM fragments and reviewed RAM-argument
  identities are separate. The remaining 152 US slots use explicitly authored
  compatibility translations, not guessed ROM addresses.

The outdoor builder also needs generated US `maps.lua` files in the isolated
LÖVE identity `ula-asian-gen2-qa`. The live runner can seed its three base game
directories from the existing `german-rom-mod-ptbr-gen1-qa` identity. Only those
disposable test saves/options are changed. No engine sources are edited.

## Build order

Run from the repository root, with `LOVE` and `LUAJIT` pointing to the local
executables used by the existing test tools. Create `build/asian-gen2` first.

```sh
python3 tools/build_asian_gen2.py gold
python3 tools/build_asian_gen2.py silver
python3 tools/build_japanese_crystal.py
python3 tools/build_asian_gen2_world.py gold
python3 tools/build_asian_gen2_world.py silver
python3 tools/build_asian_gen2_world.py crystal
python3 tools/build_asian_gen2_art.py
python3 tools/build_asian_gen2_menus.py
python3 tools/audit_asian_ui.py
```

Keep that order: text/font builders reset `assets.lua`; outdoor and title
builders add assets, and the menu builder adds native layouts last. All used
outdoor metatile and collision bytes must match the US base before an atlas
recipe is accepted. The native Pokégear tilemaps are bounded ROM RLE/flat reads.

## Live checks

For each of `gold`, `silver`, and `crystal`, run the following modes in order:

```sh
python3 tests/run_asian_gen2.py gold --mode extended
python3 tests/run_asian_gen2.py gold --mode credits
python3 tests/run_asian_gen2.py gold --mode art
python3 tests/run_asian_gen2.py gold --mode final-cold
python3 tests/run_asian_gen2.py gold --mode cold-verify
python3 tests/run_asian_gen2.py gold --mode warm
python3 tests/run_asian_gen2.py gold --mode switch-request
python3 tests/run_asian_gen2.py gold --mode switch-english
python3 tests/run_asian_gen2.py gold --mode perf-native
python3 tests/run_asian_gen2.py gold --mode perf-en
```

`extended` traverses actual purchases, menu groups and normal Oak intro.
`menus` repeats purchases and all menu checks without the intro, including
six-member teams, TM eligibility, PC submenus and a cancelled item toss.
The Asian party renderer scrolls four taller rows while retaining all six
entries and CANCEL; long pre-existing nicknames use glyph-safe scrolling.
`credits` runs the original port-credit machine, accelerating ticks between
rendered captures; `art` captures the native title/main menu. Run Crystal once
with `--mode regional` for the real Odd Egg and Eon Mail events.

`final-cold` performs the nurse, save, naming and battle script; despite its
historical name it does not itself force a cache miss. `cold-verify` clears only
compiled indexes in the isolated test identity and verifies regeneration;
`warm` requires a real cache hit. `switch-english` intentionally preserves the
selection written by the preceding switch request. Performance logs describe
360 frames of one scene, not a whole-game or process-RSS benchmark.

The live driver invokes actual interactions and compares nurse dialogue with
direct decoding of the local cartridge. The fixed engine battle templates are
authored translations, explicitly separate from that cartridge evidence.

Run the Python suite and the Lua suites described in the existing repository
QA tooling. The Asian additions are `tests/test_asian_gen2.py`,
`tests/asian_compile_unit.lua`, `tests/asian_input_unit.lua`,
`tests/asian_arguments_unit.lua`, and `tests/asian_marquee_unit.lua`.
`tools/audit_asian_ui.py` rejects missing literal Gen2 UI keys; it lists numeric,
unit, hardware and glyph-notation exceptions explicitly. Credit contributor
names remain unchanged. Authored engine translations live separately from
the ROM recipes in the three `asian_engine_*` UI modules.
`tools/asian_qa_report.py` validates the saved live markers, payload digests,
switch results and performance rows before regenerating the scoped report and
private screenshot gallery. It does not grant the overall release approval.

## Combined 1.7.0 release gate

With the existing private QA inputs staged, set `LOVE` and `LUAJIT`, then run
`python3 tests/run_release_matrix.py`. The matrix covers all 41 localized
profiles; Asian runs record runtime, driver, helper and log hashes. A partial
rerun can start at `--from-suite`, but the report still rejects any missing or
stale earlier suite. Historical PT-BR baseline evidence can also be reused by
`tests/run_merged_ptbr.py --reuse-baseline`, which verifies its original hash.

Run `tools/asian_qa_report.py` and then `tools/merged_qa_report.py` before
`tools/package.py`. The package builder verifies the current runtime fingerprint
against the merged report and verifies that the ZIP contains that same payload.
Test the ZIP with `tests/ptbr_install` using a separate `QA_INSTALL_IDENTITY`,
`QA_ENGINE`, `QA_ZIP`, and `QA_PREVIOUS_ZIP`; save the package checksum and result
in the release's package-QA document. Only publish after that check passes.
