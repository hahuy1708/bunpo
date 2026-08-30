ROOT_DECK_NAME = "JLPT N2 文法"

import hashlib

MONDAI7_DECK_ID = 2_101_001_001
MONDAI8_DECK_ID = 2_101_001_002
MONDAI9_DECK_ID = 2_101_001_003

MONDAI7_MODEL_ID = 2_101_002_001
MONDAI8_MODEL_ID = 2_101_002_002
MONDAI9_MODEL_ID = 2_101_002_003


# Kanji IDs live in a separate range so the Kanji package can be imported
# independently from the grammar package without collisions.
KANJI_ROOT_DECK_NAME = "JLPT N2 漢字 550"
KANJI_ROOT_DECK_ID = 1_935_847_000
KANJI_MODEL_ID = 1_935_847_100


def kanji_deck_id(full_deck_name: str) -> int:
    """Return a stable, positive deck ID derived from a complete deck name."""
    digest = hashlib.md5(full_deck_name.encode("utf-8")).hexdigest()
    return (1 << 30) + (int(digest, 16) % (1 << 30))
