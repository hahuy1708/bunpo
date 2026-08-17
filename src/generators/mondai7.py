import genanki

from src.config.ids import MONDAI7_DECK_ID, ROOT_DECK_NAME
from src.generators.common import escaped, note_with_guid, tags
from src.models.mondai7 import Mondai7Question
from src.templates.mondai7.model import create_model


def create_mondai7_deck() -> tuple[genanki.Deck, genanki.Model]:
    return genanki.Deck(MONDAI7_DECK_ID, f"{ROOT_DECK_NAME}::Mondai 7"), create_model()


def add_notes(deck: genanki.Deck, model: genanki.Model, questions: list[Mondai7Question]) -> None:
    for question in questions:
        fields = [escaped(question.question), *[escaped(choice) for choice in question.choices], "", "", chr(64 + question.answer), escaped(question.explanation), "", "", "", "", "", ""]
        deck.add_note(note_with_guid(model, fields, tags(7, question.period), question.id))
