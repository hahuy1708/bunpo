import contextlib
import json
import os
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path

from src.config.ids import KANJI_MODEL_ID, KANJI_ROOT_DECK_NAME
from src.generators.common import kanji_group, kanji_tags
from src.generators.kanji import format_question
from src.kanji import build
from src.models.kanji import KanjiQuestion


VALID_QUESTION = {
    "id": "N2K-CH01-M1-01", "chapter": 1, "kanji_range": "001-072",
    "mondai": 1, "no": 1, "sentence": "漢字を読む", "underline": "漢字",
    "choices": ["かんじ", "かんし", "かじ", "かん"], "answer": 1,
}


class KanjiValidationTests(unittest.TestCase):
    def test_question_validation(self):
        self.assertEqual(KanjiQuestion.from_dict(VALID_QUESTION).id, "N2K-CH01-M1-01")
        for key in ("id", "choices", "answer"):
            source = VALID_QUESTION.copy()
            source.pop(key)
            with self.assertRaisesRegex(ValueError, "missing fields"):
                KanjiQuestion.from_dict(source)

        source = VALID_QUESTION | {"choices": ["A"]}
        with self.assertRaisesRegex(ValueError, "exactly 4"):
            KanjiQuestion.from_dict(source)
        source = VALID_QUESTION | {"answer": 5}
        with self.assertRaisesRegex(ValueError, "answer must be 1-4"):
            KanjiQuestion.from_dict(source)
        source = VALID_QUESTION | {"chapter": 9}
        with self.assertRaisesRegex(ValueError, "chapter"):
            KanjiQuestion.from_dict(source)
        source = VALID_QUESTION | {"mondai": 5}
        with self.assertRaisesRegex(ValueError, "mondai"):
            KanjiQuestion.from_dict(source)

    def test_underline_rules(self):
        for mondai in (1, 2, 4):
            source = VALID_QUESTION | {"mondai": mondai, "underline": None}
            with self.assertRaisesRegex(ValueError, "underline is required"):
                KanjiQuestion.from_dict(source)
        source = VALID_QUESTION | {"mondai": 3, "underline": "漢字"}
        with self.assertRaisesRegex(ValueError, "must not have underline"):
            KanjiQuestion.from_dict(source)

    def test_formatting_groups_and_tags(self):
        self.assertEqual([kanji_group(mondai) for mondai in range(1, 5)], [
            "doc_trong_cau", "viet_kanji", "doc_tu_don", "viet_kanji",
        ])
        self.assertEqual(kanji_tags(2, 4, "073-138"), ["chapter2", "mondai4", "viet_kanji"])
        writing = format_question("漢字を書く", "漢字", 2)
        self.assertIn("<u>漢字</u>", writing)
        self.assertNotIn("<u>", format_question("漢字", None, 3))


class KanjiBuildTests(unittest.TestCase):
    def test_smoke_build_has_expected_decks_notes_and_model(self):
        with tempfile.TemporaryDirectory() as directory:
            package = build(output_path=Path(directory) / "kanji.apkg")
            self.assertGreater(package.stat().st_size, 0)
            with zipfile.ZipFile(package) as archive, archive.open("collection.anki2") as collection_file:
                with tempfile.NamedTemporaryFile(suffix=".anki2", delete=False) as temp_collection:
                    temp_collection.write(collection_file.read())
                    collection_path = Path(temp_collection.name)
            try:
                with sqlite3.connect(collection_path) as database:
                    decks = json.loads(database.execute("select decks from col").fetchone()[0])
                    models = json.loads(database.execute("select models from col").fetchone()[0])
                    note_count = database.execute("select count(*) from notes").fetchone()[0]
                    deck_counts = dict(database.execute("select did, count(*) from cards group by did"))
            finally:
                with contextlib.suppress(FileNotFoundError, PermissionError):
                    os.unlink(collection_path)

            kanji_decks = [deck for deck in decks.values() if deck["name"].startswith(KANJI_ROOT_DECK_NAME)]
            self.assertEqual(len(kanji_decks), 33)
            self.assertEqual(note_count, 320)
            self.assertEqual(models[str(KANJI_MODEL_ID)]["name"], "JLPT N2 Kanji 550 MCQ")
            for chapter in range(1, 9):
                prefix = f"{KANJI_ROOT_DECK_NAME}::Chapter {chapter:02d}"
                leaves = [deck for deck in kanji_decks if deck["name"].startswith(prefix + " (") and deck["name"].count("::") == 2]
                self.assertEqual(len(leaves), 3)
                writing = next(deck for deck in leaves if deck["name"].endswith("Mondai 2+4"))
                self.assertEqual(deck_counts.get(int(writing["id"])), 20)


if __name__ == "__main__":
    unittest.main()
