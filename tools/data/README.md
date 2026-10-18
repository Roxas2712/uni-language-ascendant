# Spanish Yellow address corrections

`yellow-es-extra-addresses.json` contains factual bank/address pairs for the
exact Spanish Yellow SHA-1 `1dc242039218fba50928d1afb66b70565b6b9daf`.
It contains no translated text. `build_european_gb.py` applies these after the
published Spanish table-layout metadata, before compiling ROM spans.

The initial missing-label runs were read sequentially between adjacent known
text anchors. A run is accepted only if its terminating record closes on the
next anchor (apart from text-end padding). Six harder entries were recovered
from retail `text_far` references, using either a unique normalized surrounding
CPU sequence or a contiguous wrapper table with two known neighbours. These
include three overflow strings in bank $30; carrying over the original bank
would be wrong.

Additional cross-checks:

- `_CinnabarGymQuizShortIntroText`: a unique normalized `ld hl, wrapper`
  reference relocates US flat $1E40B to ES $1E40C. The adjacent three five-byte
  wrappers in the exact ES ROM are at $1E402/$1E407/$1E40C and point to
  $27:$69CA/$6A9A/$6B81. This also corrects the existing intro address, which
  previously selected its dummy variant.
- `_LinkCableHelpText1` has one exact far wrapper in ES at flat $5DD08.
  Its consecutive `LinkCableHelpText2` wrapper at $5DD0D points to $30:$4F1B.
- `_WildMonAppearedText` and `_HookedMonAttackedText` are neighbours in an
  engine wrapper table validated by two existing known destinations.
- The Spanish Safari gate prints a literal 500 instead of the US runtime
  decimal field; the builder handles that specific regional variant.

These additions fill all 2,710 named dialogue labels. This is not an exact
Spanish Yellow source rebuild or a proof that every pre-existing factual
address in the external metadata is correct. The preview still needs broader
scene and whole-game review.
