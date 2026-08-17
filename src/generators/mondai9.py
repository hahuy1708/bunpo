import genanki

from src.config.ids import MONDAI9_DECK_ID, ROOT_DECK_NAME
from src.generators.common import escaped, note_with_guid, tags
from src.models.mondai9 import Mondai9Question
from src.templates.mondai9.model import create_model


def create_mondai9_deck() -> tuple[genanki.Deck, genanki.Model]:
    return genanki.Deck(MONDAI9_DECK_ID, f"{ROOT_DECK_NAME}::Mondai 9"), create_model()


def add_notes(deck: genanki.Deck, model: genanki.Model, questions: list[Mondai9Question]) -> None:
    for question in questions:
        fields = [escaped(question.context)]
        for subquestion in question.questions:
            fields.extend(escaped(choice) for choice in subquestion.choices)
        fields.extend(chr(64 + subquestion.answer) for subquestion in question.questions)
        deck.add_note(note_with_guid(model, fields, tags(9, question.period), question.id))
