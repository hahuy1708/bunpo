import json
from pathlib import Path

import genanki

from src.generators import mondai7, mondai8, mondai9
from src.models.mondai7 import Mondai7Question
from src.models.mondai8 import Mondai8Question
from src.models.mondai9 import Mondai9Question

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATHS = {
    "mondai7": PROJECT_ROOT / "data/mondai7/questions.json",
    "mondai8": PROJECT_ROOT / "data/mondai8/questions.json",
    "mondai9": PROJECT_ROOT / "data/mondai9/questions.json",
}
OUTPUT_PATH = PROJECT_ROOT / "output/JLPT_N2_文法.apkg"


def load_questions(path: Path, parser):
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: invalid JSON: {error.msg}") from error
    if not isinstance(raw, list):
        raise ValueError(f"{path}: root JSON value must be an array")
    return [parser(item) for item in raw]


def build(output_path: Path = OUTPUT_PATH) -> Path:
    m7_questions = load_questions(DATA_PATHS["mondai7"], Mondai7Question.from_dict)
    m8_questions = load_questions(DATA_PATHS["mondai8"], Mondai8Question.from_dict)
    m9_questions = load_questions(DATA_PATHS["mondai9"], Mondai9Question.from_dict)

    deck7, model7 = mondai7.create_mondai7_deck()
    deck8, model8 = mondai8.create_mondai8_deck()
    deck9, model9 = mondai9.create_mondai9_deck()
    # Keep all three Note Types in the package even while a data file is empty.
    deck7.add_model(model7)
    deck8.add_model(model8)
    deck9.add_model(model9)
    mondai7.add_notes(deck7, model7, m7_questions)
    mondai8.add_notes(deck8, model8, m8_questions)
    mondai9.add_notes(deck9, model9, m9_questions)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package([deck7, deck8, deck9]).write_to_file(output_path)
    return output_path


if __name__ == "__main__":
    path = build()
    print(f"Built {path}")
