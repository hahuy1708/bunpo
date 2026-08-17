import genanki

from src.config.ids import MONDAI8_DECK_ID, ROOT_DECK_NAME
from src.generators.common import escaped, note_with_guid, tags
from src.models.mondai8 import Mondai8Question
from src.templates.mondai8.model import create_model


def create_mondai8_deck() -> tuple[genanki.Deck, genanki.Model]:
    return genanki.Deck(MONDAI8_DECK_ID, f"{ROOT_DECK_NAME}::Mondai 8"), create_model()


def ordered_fragments(question: Mondai8Question) -> str:
    return " → ".join(question.choices[number] for number in question.answer_order)


def add_notes(deck: genanki.Deck, model: genanki.Model, questions: list[Mondai8Question]) -> None:
    for question in questions:
        note_text = (
            f"<b>Full sentence</b><br>{escaped(question.full_sentence)}<br><br>"
            f"<b>Correct order</b>: {escaped(ordered_fragments(question))}<br>"
            f"<b>★ answer</b>: {question.star_choice_number}"
        )
        fields = [
            escaped(question.sentence_all_blanked),
            ",,".join(escaped(question.choices[str(number)]) for number in range(1, 5)),
            note_text,
        ]
        deck.add_note(note_with_guid(model, fields, tags(8, question.period), question.id))
