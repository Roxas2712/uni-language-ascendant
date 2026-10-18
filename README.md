# Uni-Language Ascendant

Standalone language mod for **Gen1Recomp**, based on the Pokémon Gen 1
Recompilation Project by BOIS CLUB GAMES, LLC
(https://github.com/bryanthaboi/gen1recomp).

## Combined preview 1.6.0-merged-preview.1

Combines the released **PT-BR 1.5.2** runtime with **European preview 5**.
There are **38 localized profiles** across eleven editions, plus the English base.
The optimized binary cache, lazy graphics loading, disabled-language picker,
European menu/graphic translations and PT-BR corrections are included together.

| Editions | Game languages besides English |
| --- | --- |
| Red, Yellow | German, Brazilian Portuguese, Spanish |
| Blue, Ruby, Sapphire | German, Brazilian Portuguese |
| Gold, Emerald | German, Brazilian Portuguese, Spanish, French, Italian |
| Silver, LeafGreen | German, Brazilian Portuguese, Spanish, French |
| Crystal, FireRed | German, Brazilian Portuguese, Spanish, Italian |

Ten independently selectable menu languages: English, German, French, Italian,
Spanish, Japanese, Korean, Simplified Chinese, Traditional Chinese and Brazilian
Portuguese. Menu support does not imply a game-language profile exists.
Unavailable game languages remain visible and disabled; missing imports and
unsupported profiles have distinct explanations.

## Install the combined preview

1. Import the exact supported English US base game in Gen1Recomp.
2. Install `dist/uni-language-ascendant-1.6.0-merged-preview.1.zip` through the mod
   manager and enable it for the desired game.
3. Import the exact language ROM under **Uni-Language Ascendant → Imports**.
4. Launch, select a menu language and then an available game language.

The ZIP is built locally with `python3 tools/package.py`; this combined preview
has not been published as a GitHub release. The exact ROM versions and SHA-1
identities are listed in [the ROM checklist](mod/ROM-Liste.html) and
[the source catalog](tools/rom_requirements.json). File names do not identify a
revision. Sapphire PT-BR reuses the exact Ruby PT-BR source import with separate
Sapphire recipes and authored text. FRLG PT-BR fanpatch sources use revision 1.1;
the recompiler runtime uses its supported US 1.0 base. Do not interchange them.
[Fan translation sources and patch identities](tools/ptbr_sources.json) retain
their attribution. No ROM, fanpatch, save or compilation cache is distributed.

**Updates preserve imported ROMs, preferences, intro state and saves.** The first
launch rebuilds the language cache once. Uninstalling deletes the mod profile;
reinstalling starts fresh. The intro runs once per profile. Back, Reset profile
and the ROM requirements view remain available. Missing saved imports fall back
to English; changing the active game language requires a restart.

## Verification

Fresh integration checks and exact payload fingerprints are recorded in
[MERGE-QA.json](mod/MERGE-QA.json), with readable scope in
[MERGED-PREVIEW.md](mod/MERGED-PREVIEW.md). They cover the combined payload.

The prior branches' evidence is retained with its original version:

- [European preview 5](mod/EUROPE-PREVIEW.md) and [European QA](mod/EUROPE-QA.json).
- [PT-BR gameplay report](mod/PT-BR.html) and [1.5.1 QA](docs/PT-BR-QA.json).
- [Cache optimization evidence](docs/Optimization-1.5.1.json) and
  [1.5.2 language-picker release checks](docs/Release-1.5.2.json).

Those historical reports are not fresh merged-version results. Scoped fixtures
prepare maps, inventory or Pokémon; they do not inject displayed dialogue.
No complete story playthrough, independent native-speaker certification,
Windows/Linux integration test or two-device multiplayer test is claimed.
The European UI source audit covers a defined set of engine strings; it is not
an assertion that every possible dialogue branch has been reviewed.

Remaining language profiles and exact future inputs are listed in
[Weitere-Sprachen.html](mod/Weitere-Sprachen.html). Available profiles are filtered
out of that checklist automatically.

## License

GPLv3 applies. Existing source and attribution requirements are preserved;
see [LICENSE.MD](LICENSE.MD), [LICENSE-POLICY.md](LICENSE-POLICY.md) and
[VENDOR.md](mod/VENDOR.md). Intro assets and bundled font notices remain included.
