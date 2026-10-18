# Combined preview 1.6.0-merged-preview.1

PT-BR 1.5.2 (e79e37d) and European preview 5 (9e846d9) are combined.
38 localized profiles across eleven editions; the English base remains available.
The ten-language picker, exact ROM checks, binary cache, lazy assets, native
European UI/graphics and authored PT-BR corrections are included.

Fresh integration checks are recorded in MERGE-QA.json. The final matrix has
85 short automated process runs: 24 European GBA cold/warm checks, 10 English/
disabled restarts, 9 European GB/GBC font/catalog runs, 22 PT-BR cold/warm runs,
3 representative PT-BR gameplay fixtures (Red, Gold, Emerald), 6 German GB/GBC
payload checks and 11 per-edition language-picker checks. All 38 profiles are
started. There are also 70 Python tests, 14 Lua groups, binary-cache integrity
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

The ZIP update from 1.5.2 is checked in a dedicated installation test, including
preferences, intro status, import and save sentinels, uninstall and reinstall.
 Historical evidence in
EUROPE-QA.json (preview 5), PT-BR.html and docs/PT-BR-QA.json (1.5.1) describes the
original branches and must not be read as fresh tests of this merged payload.
There are no full-story playthroughs or independent native-speaker certification.
Windows/Linux and two-device multiplayer were not tested in this integration.
The first launch rebuilds the language cache. Updates preserve imported ROMs,
preferences and saves. No ROM, fanpatch, save or compilation cache is distributed.

GPLv3 and the existing attribution requirements remain in force; see LICENSE-POLICY.md.
