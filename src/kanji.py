import json
from pathlib import Path

import genanki

from src.config.ids import KANJI_ROOT_DECK_ID, KANJI_ROOT_DECK_NAME
from src.generators import kanji as kanji_gen
from src.models.kanji import KanjiQuestion


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data/kanji_550/questions.json"
OUTPUT_PATH = PROJECT_ROOT / "output/N2_漢字_550.apkg"


def load_questions(path: Path) -> list[KanjiQuestion]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: invalid JSON: {error.msg}") from error
    if not isinstance(raw, list):
        raise ValueError(f"{path}: root JSON value must be an array")
    return [KanjiQuestion.from_dict(item) for item in raw]


def build(data_path: Path = DATA_PATH, output_path: Path = OUTPUT_PATH) -> Path:
    questions = load_questions(data_path)
    model = kanji_gen.create_kanji_model()
    chapters = sorted({(question.chapter, question.kanji_range) for question in questions})
    chapter_decks: list[genanki.Deck] = []
    decks_by_chapter: dict[int, dict[str, genanki.Deck]] = {}
    for chapter, kanji_range in chapters:
        chapter_deck, subdecks = kanji_gen.create_chapter_decks(chapter, kanji_range)
        chapter_decks.append(chapter_deck)
        decks_by_chapter[chapter] = subdecks

    count = kanji_gen.add_notes(decks_by_chapter, model, questions)
    root_deck = genanki.Deck(KANJI_ROOT_DECK_ID, KANJI_ROOT_DECK_NAME)
    all_decks = [root_deck, *chapter_decks, *(deck for subdecks in decks_by_chapter.values() for deck in subdecks.values())]
    for deck in all_decks:
        deck.add_model(model)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(all_decks).write_to_file(output_path)
    # Keep CLI builds working in legacy Windows consoles that cannot render Japanese.
    print(f"Built Kanji package ({count} notes, {len(all_decks)} decks)")
    return output_path


if __name__ == "__main__":
    build()
