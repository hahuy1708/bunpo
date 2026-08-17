from pathlib import Path

import genanki

from src.config.ids import MONDAI9_MODEL_ID

_HERE = Path(__file__).parent
FIELDS = ["context"] + [f"q{number}_option{letter}" for number in range(1, 5) for letter in "ABCD"] + [f"q{number}_answer" for number in range(1, 5)]


def create_model() -> genanki.Model:
    return genanki.Model(
        MONDAI9_MODEL_ID,
        "JLPT N2 M9 Context MCQ",
        fields=[{"name": name} for name in FIELDS],
        templates=[{"name": "Card 1", "qfmt": (_HERE / "front.html").read_text(encoding="utf-8"), "afmt": (_HERE / "back.html").read_text(encoding="utf-8")}],
        css=(_HERE / "style.css").read_text(encoding="utf-8"),
    )
