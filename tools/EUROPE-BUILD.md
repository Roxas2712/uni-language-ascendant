# European profile build inputs

All ROMs and reconstructed source trees stay under ignored `build/` or outside
the checkout. Nothing in this workflow fetches or distributes cartridge dumps.

`build/european-inputs.json` is a JSON array of records with `game`, `language`,
`file`, `sha1`, `md5`, `size`; `file` is the developer's private absolute path.
`build/gb-rom-inventory.json` records the corresponding private US bases.
Every ROM input is checked against its pinned exact checksum before use.

The source revisions and attribution are listed in `mod/VENDOR.md`.

- FRLG: `build_european_frlg.py GAME LANGUAGE` consumes exact target and German
  ELF/GBA builds under `build/pokefirered-europe`, plus exported stable profile
  metadata (`GAME-metadata.json`, `GAME_assets-metadata.json`,
  `GAME_world-metadata.json`, `GAME-table-metadata.json`). ELF symbol extents,
  local scopes, table order and rebuilt ROM hashes constrain relocation.
- Gen2: `relocate_gen2.py GAME LANGUAGE` consumes the pinned engine's ROM
  manifest, exported opcode definitions and the valid native script-key list.
  Full exact US symbol files are under `build/pokegold` / `build/pokecrystal`.
  Crystal ES additionally uses exact rebuilt Spanish symbol identities exported
  into `build/crystal-es-symbols.json` and
  `build/crystal-es-authoritative-offsets.json`. Crystal IT composes US -> ES ->
  IT, with event graph checks, complete text-bank grammar and explicit regional
  empty-mobile / five simplified-menu-text exceptions. Build ES before IT.
- `build_european_gb.py GAME LANGUAGE` compiles the audited relocation JSON into
  address-only Lua catalogs. It checks trainer party identity, name-table
  topology, full landmark coordinates, metric data bounds and font glyphs.
  Gen1 additionally consumes exported factual `GAME-es-source-metadata.json`;
  Red uses its byte-identical rebuilt full Spanish symbol table, and Yellow
  applies the documented address corrections in `tools/data/`.
- `build_rom_list.py` and `build_language_needs.py` regenerate supported and
  missing-input documents. The latter needs the three local No-Intro metadata
  files under `build/language-references` (checksums are in language_needs.json).
- `tests/run_european_languages.py` uses the isolated
  `ula-europe-expansion-qa` LÖVE identity. Populate its US import caches first,
  and supply the local engine executable through `LOVE`. The script stages
  only the exact requested private language ROMs and creates QA saves.
- `tools/package.py` creates a runtime-only ZIP, verifies its archive integrity
  and rejects ROM/save paths. Existing GPL and font license files are included.

The development tools fail on unexpected layouts rather than filling addresses
from a similar revision. Some special fixed-slot sections also use explicit
bounds/glyph checks; these checks do not replace complete playthrough testing.

## Preview-4 GBA completion

- `build_gba_ui.py` compiles `translations/gba/ui-extra.tsv` and
  `ui-common-de.tsv`; the latter reuses the reviewed shared ES/FR/IT catalog.
  Placeholders and paragraph controls are build invariants.
- `audit_gba_ui.py` inventories the pinned engine's fixed GBA `Strings` calls.
  It deliberately does not claim to identify every dynamic or raw draw string.
- `tests/run_gba_completion.py` uses `ula-gba-completion-qa` only. It stages
  checksum-verified private inputs, clones the existing private US caches, and
  runs all 12 profiles cold/warm. Run the five `GAME_de` profiles additionally
  with `--modes english,disabled`. Set `LOVE` to the local engine executable.
- `tests/gba_policy_unit.lua` runs under LuaJIT in the pinned engine directory.
  It verifies explicit exception semantics and unknown-key reporting.
- `gba_qa_report.py` requires the 34 successful current-fingerprint live runs,
  the source audit and `build/gba-completion-unit.log`. It verifies the generated
  catalog against its editorial source, then produces the current report.
  Preview-3 GB results are explicitly inherited only after checking unchanged
  GB/profile sources and the shared startup path against commit 8d22d8f.
- Run `package.py` after report generation. The `mod/gba/` runtime modules
  and catalog are on its explicit allowlist; private caches remain excluded.
