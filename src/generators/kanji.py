import html

import genanki

from src.config.ids import KANJI_MODEL_ID, KANJI_ROOT_DECK_NAME, kanji_deck_id
from src.generators.common import kanji_group, kanji_tags, note_with_guid
from src.models.kanji import KanjiQuestion
from src.templates.mondai7.model import create_mcq_model


SUBDECK_LABELS = {
    "doc_trong_cau": "Mondai 1",
    "doc_tu_don": "Mondai 3",
    "viet_kanji": "Mondai 2+4",
}


def format_question(sentence: str, underline: str | None, mondai: int) -> str:
    safe_sentence = html.escape(sentence, quote=False)
    if underline:
        safe_underline = html.escape(underline, quote=False)
        safe_sentence = safe_sentence.replace(safe_underline, f"<u>{safe_underline}</u>", 1)
    return f'<div class="sentence">{safe_sentence}</div>'


def create_kanji_model() -> genanki.Model:
    return create_mcq_model(KANJI_MODEL_ID, "JLPT N2 Kanji 550 MCQ")


def create_chapter_decks(chapter: int, kanji_range: str) -> tuple[genanki.Deck, dict[str, genanki.Deck]]:
    chapter_name = f"{KANJI_ROOT_DECK_NAME}::Chapter {chapter:02d} ({kanji_range})"
    chapter_deck = genanki.Deck(kanji_deck_id(chapter_name), chapter_name)
    subdecks = {
        group: genanki.Deck(kanji_deck_id(f"{chapter_name}::{label}"), f"{chapter_name}::{label}")
        for group, label in SUBDECK_LABELS.items()
    }
    return chapter_deck, subdecks


def add_notes(decks_by_chapter: dict[int, dict[str, genanki.Deck]], model: genanki.Model,
              questions: list[KanjiQuestion]) -> int:
    for question in questions:
        fields = [
            format_question(question.sentence, question.underline, question.mondai),
            *[html.escape(choice, quote=False) for choice in question.choices],
            "", "", chr(64 + question.answer), html.escape(question.explanation, quote=False),
            "", "", "", "", "", "",
        ]
        note = note_with_guid(model, fields, kanji_tags(question.chapter, question.mondai, question.kanji_range), question.id)
        decks_by_chapter[question.chapter][kanji_group(question.mondai)].add_note(note)
    return len(questions)
