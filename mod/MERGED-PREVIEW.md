# Release 1.7.0 – integration scope

PT-BR 1.5.2 (e79e37d), the European language expansion and Asian Gen2 profiles are combined.
41 localized profiles across eleven editions; the English base remains available.
The ten-language picker, exact ROM checks, binary cache, lazy assets, native
European UI/graphics and authored PT-BR corrections are included.

Fresh integration checks are recorded in MERGE-QA.json. The final matrix has
113 automated process runs: 24 European GBA cold/warm checks, 10 English/
disabled restarts, 9 European GB/GBC font/catalog runs, 22 PT-BR cold/warm runs,
3 representative PT-BR gameplay fixtures (Red, Gold, Emerald), 6 German GB/GBC
payload checks and 11 per-edition language-picker checks, plus 28 Asian Gen2 runs covering actual
dialogues, gameplay, menus, titles, credits, cache regeneration and language switching.
All 41 profiles are started. There are also 85 Python tests, 18 Lua groups, binary-cache integrity
checks and bounded engine UI source audits.

All eleven PT-BR payloads are compared with 11 reference starts of committed
1.5.2: 159,807 effective registry entries and 6,797 assets. Equivalent manifest
ordering and contest tile packing are checked explicitly. Warm payloads match
cold payloads. The merge also corrects the final coverage counter after authored
PT-BR text is applied; this changes report metadata, not displayed text.

The nine FRLG PT-BR entries still listed as unmapped in the original report are
preserved: five empty placeholders/dummies, two line-break helpers, one space
and one decorative ?{PKMN}? control string. They are not untranslated dialogue.
The corresponding original registry values were inspected separately.

The ZIP update from the previous 1.6.0 preview is checked in a dedicated installation test, including
preferences, intro status, import and save sentinels, uninstall and reinstall.
Historical evidence in
EUROPE-QA.json (preview 5), PT-BR.html and docs/PT-BR-QA.json (1.5.1) describes the
original branches and must not be read as fresh tests of this merged payload.
There are no full-story playthroughs or independent native-speaker certification.
Windows/Linux and two-device multiplayer were not tested in this integration.
The first launch rebuilds the language cache. Updates preserve imported ROMs,
preferences and saves. No ROM, fanpatch, save or compilation cache is distributed.

GPLv3 and the existing attribution requirements remain in force; see LICENSE-POLICY.md.
