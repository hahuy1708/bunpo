from pathlib import Path

import genanki

from src.config.ids import MONDAI7_MODEL_ID

_HERE = Path(__file__).parent


def create_mcq_model(model_id: int, model_name: str) -> genanki.Model:
    """Create the interactive MCQ model used by grammar and Kanji packages."""
    return genanki.Model(
        model_id,
        model_name,
        fields=[{"name": name} for name in (
            "question", "optionA", "optionB", "optionC", "optionD", "optionE", "optionF",
            "answer", "note", "noteA", "noteB", "noteC", "noteD", "noteE", "noteF",
        )],
        templates=[{
            "name": "Card 1",
            "qfmt": (_HERE / "front.html").read_text(encoding="utf-8"),
            "afmt": (_HERE / "back.html").read_text(encoding="utf-8"),
        }],
        css=(_HERE / "style.css").read_text(encoding="utf-8"),
    )


def create_model() -> genanki.Model:
    return create_mcq_model(MONDAI7_MODEL_ID, "JLPT N2 M7 MCQ")
