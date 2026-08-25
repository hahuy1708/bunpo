import contextlib
import unittest
import json
import os
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from src.generators.common import note_with_guid
from src.generators.mondai8 import ordered_fragments
from src.config.ids import ROOT_DECK_NAME
from src.models.mondai7 import Mondai7Question
from src.models.mondai8 import Mondai8Question
from src.models.mondai9 import Mondai9Question
from src.templates.mondai7.model import create_model as create_m7_model
from src.main import build


class ValidationTests(unittest.TestCase):
    def test_m7_validation_and_stable_guid(self):
        source = {"id": "M7-1", "period": "2020.07", "no": 1, "question": "Q", "choices": ["A", "B", "C", "D"], "answer": 2, "explanation": "E"}
        question = Mondai7Question.from_dict(source)
        model = create_m7_model()
        first = note_with_guid(model, ["Q", "A", "B", "C", "D", "", "", "B", "", "", "", "", "", "", ""], [], question.id)
        second = note_with_guid(model, ["Q", "A", "B", "C", "D", "", "", "B", "", "", "", "", "", "", ""], [], question.id)
        self.assertEqual(first.guid, second.guid)
        source["choices"] = ["A"]
        with self.assertRaisesRegex(ValueError, "exactly 4"):
            Mondai7Question.from_dict(source)

    def test_m8_order(self):
        question = Mondai8Question.from_dict({"index": 1, "period": "2010.07", "no": 45, "sentence_all_blanked": "Q", "choices": {"1": "A", "2": "B", "3": "C", "4": "D"}, "answer_order": "2341", "star_position_in_blanks": 3, "star_choice_number": 4, "full_sentence": "Answer"})
        self.assertEqual(ordered_fragments(question), "B → C → D → A")

    def test_m9_validation(self):
        source = {"id": "M9-1", "period": "2020.07", "no": 1, "context": "text", "questions": [{"id": str(i), "choices": ["A", "B", "C", "D"], "answer": 1} for i in range(4)]}
        self.assertEqual(len(Mondai9Question.from_dict(source).questions), 4)
        source["questions"] = source["questions"][:3]
        with self.assertRaisesRegex(ValueError, "exactly 4"):
            Mondai9Question.from_dict(source)

    def test_smoke_build_includes_three_decks_and_models(self):
        with tempfile.TemporaryDirectory() as directory:
            package = build(Path(directory) / "test.apkg")
            self.assertGreater(package.stat().st_size, 0)
            with zipfile.ZipFile(package) as archive:
                with archive.open("collection.anki2") as collection_file:
                    with tempfile.NamedTemporaryFile(suffix=".anki2", delete=False) as temp_collection:
                        temp_collection.write(collection_file.read())
                        collection_path = Path(temp_collection.name)
            try:
                with sqlite3.connect(collection_path) as database:
                    decks = json.loads(database.execute("select decks from col").fetchone()[0])
                    models = json.loads(database.execute("select models from col").fetchone()[0])
            finally:
                with contextlib.suppress(FileNotFoundError, PermissionError):
                    os.unlink(collection_path)
            expected_decks = {
                f"{ROOT_DECK_NAME}::Mondai 7",
                f"{ROOT_DECK_NAME}::Mondai 8",
                f"{ROOT_DECK_NAME}::Mondai 9",
            }
            self.assertEqual({deck["name"] for deck in decks.values() if deck["name"].startswith(ROOT_DECK_NAME)}, expected_decks)
            self.assertEqual({model["name"] for model in models.values()}, {"JLPT N2 M7 MCQ", "JLPT N2 M8 Ordering", "JLPT N2 M9 Context MCQ"})


if __name__ == "__main__":
    unittest.main()
