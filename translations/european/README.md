# Supplemental European GB/GBC interface

`gb-ui.json` holds 856 English engine UI keys with Spanish, French and Italian
values. It supplements the retail dialogue/name recipes; it is not a dump of ROM
text. The first 70 phrases were authored for preview 1. Preview 2 adds
machine-assisted drafts of public engine UI literals, with manual terminology,
compact fixed-field labels and menu corrections. It has not received a complete
native-speaker editorial review.

`gb-ui-overrides.tsv` is the manual correction layer, separated with `|` so that
font/control markup stays legible. Literal `\n` and `\f` represent line/page breaks.
Later rows override earlier rows. Run these offline after editing:

```sh
python3 tools/build_european_ui.py
LUAJIT=/path/to/luajit python3 tools/sync_european_ui.py
LUAJIT=/path/to/luajit python3 tests/european_ui_catalog.py
```

The validator checks printf fields, brace/angle control identities and nonempty
values; the test also checks the actual fixed columns in the engine and all nine
generated profiles. Runtime formatting preserves inserted player names/numbers.
No network translation service is used by either the compiler or the mod.

Graphics development uses the exact private ROMs and pinned engine under ignored
`build/`. `build_european_gb_gfx.py` derives target symbol locations, runs
`export_european_gfx.lua` in a windowless LÖVE harness, and compiles exported
images into ROM-address/tile/palette recipes. `build_european_gb_world.py` handles
world sheets and Crystal's regional visual metatiles; Gen1 Yellow's title has a
separate tilemap builder. They require the private audit/intermediate files,
Pillow, the `lzscan.c` helper, `LUAJIT`, and `LOVE` for exports. They are developer
tools, not a general ROM importer. Run world/title additions after the base
profile builder, which initializes the asset catalogs. UI synchronization
preserves the asset catalogs.

`tests/european_gfx_roundtrip.lua` compares reconstructed PNG pixels to the direct
cartridge extraction (including alpha/flips). `tests/european_gb_menus.lua` opens
real menus in the separate QA identity; `tests/european_gb_live.lua` checks world,
dialogue, Pokédex and unchanged species/move mechanics. Private ROMs, graphics,
saves and test screenshots are excluded from Git and the installable package.
