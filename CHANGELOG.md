# Changelog

## 1.7.0

- Publish the combined language package as a regular release, with 41 localized
  profiles across eleven editions and ten selectable menu languages.
- Add Japanese Crystal and Korean Gold/Silver with native text, fonts, naming,
  title/menu graphics and overworld signage.
- Cover all 508 previously unfilled Crystal slots: 356 additional native ROM
  mappings and 152 explicitly authored US-compatibility translations.
- Fit Asian text in party, PC, Pack, summary, battle and Pokédex screens; support
  taller Hangul, Japanese voiced marks and native text-parameter order.
- Verify the current package across all profiles and retain PT-BR payloads,
  optimized cache behavior, disabled-language choices and exact ROM identities.
- Record actual game scenarios and scope limits in MERGE-QA.json / ASIAN-QA.json;
  no full-story playthrough or regional-mechanics replacement is claimed.

## 1.6.0-merged-preview.1

- Combine European preview 5 with PT-BR 1.5.2: 38 localized profiles.
- Preserve optimized caches and disabled language choices.
- Record fresh integration checks separately from historical branch QA.

## 1.4.3-europe-preview.5

- Translate the remaining shared mod-contribution diagnostic in ES/FR/IT.
- Improve the French boot failure and remove a Spanish gender assumption
  in the link-partner busy message.
- Screen all supplemental catalog cells and rerun short font/profile checks.
- Keep complete playthrough and independent native-speaker review claims open.

## 1.4.3-europe-preview.4

- Add 245 supplemental GBA UI entries in German, Spanish, French and Italian.
- Use regional item names in FRLG script buffers and Pokemon Jump prizes;
  remove English-only plural suffix helpers.
- Preserve credit identities explicitly, translate missing RS credit headings,
  and distinguish these categories from native ROM text coverage.
- Correct the SPEED settings/stat meaning collision and dynamic zoom labels.
- Add bounded source, real-font/menu, native credit-pointer, cold/warm cache,
  save and English/disabled lifecycle checks for all twelve GBA profiles.
## 1.5.1

- Load compiled operations from a bounded binary data format and defer large
  Gen3 address/translation tables until a cache rebuild is actually needed.
- Remove superseded operation history while preserving final values, patch
  chains and first-touch ordering.
- Keep large Gen3 raw graphics losslessly compressed until first use, then reuse
  the decoded bytes. Full exported asset inspection still exposes every file.
- Validate stored and expanded cache payloads before applying translations;
  damaged caches rebuild automatically.
- Rebuild the language cache once after updating; preserve imported ROMs,
  language choices, intro status and saves.
- Add complete before/after content comparison and controlled release-to-release
  performance evidence alongside the native gameplay checks.

## 1.4.2

- Hide game languages without a supported, imported ROM for the selected edition
  in both the startup picker and launcher mod options.
- Fall back to English when a saved language or launcher override is unavailable.
- Keep all nine menu languages and the ROM requirements list accessible.
- Cover missing imports, other-edition imports, alternate revisions and fallback
  selection in unit and live tests. Wait for actual rendering before clicking
  the language-page controls in the UI test.
- Replace developer-specific executable paths with configurable environment
  settings in the test and profile tools.

## 1.4.1

- Correct and complete Emerald French, Italian and Spanish text address mappings.
- Verify 176 added or changed mappings against decoded ROM data on cold and warm
  loads. Each language maps 15,653 of 15,655 text keys, with two credits exceptions.
- Handle localized glyph cells and preserve decoder state after extraction.

## 1.4.0

- Add Emerald French, Italian and Spanish revision-0 profiles.
- Include nine menu locales, shared Ascendant first-run intro, Back and Reset.
- Support German language profiles across all eleven Gen1–Gen3 editions.

