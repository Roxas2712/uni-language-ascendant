# Changelog

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

