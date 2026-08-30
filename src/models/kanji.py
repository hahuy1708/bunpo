from dataclasses import dataclass


CHAPTER_RANGE = range(1, 9)
MONDAI_RANGE = (1, 2, 3, 4)
MONDAI_NEEDS_UNDERLINE = (1, 2, 4)


@dataclass(frozen=True)
class KanjiQuestion:
    id: str
    chapter: int
    kanji_range: str
    mondai: int
    no: int
    sentence: str
    underline: str | None
    choices: list[str]
    answer: int
    explanation: str = ""

    @classmethod
    def from_dict(cls, value: dict) -> "KanjiQuestion":
        required = ["id", "chapter", "kanji_range", "mondai", "no", "sentence", "choices", "answer"]
        missing = [key for key in required if key not in value]
        if missing:
            raise ValueError(f"{value.get('id', '?')}: missing fields {missing}")

        qid = value["id"]
        if value["chapter"] not in CHAPTER_RANGE:
            raise ValueError(f"{qid}: chapter must be in {CHAPTER_RANGE}")
        if value["mondai"] not in MONDAI_RANGE:
            raise ValueError(f"{qid}: mondai must be one of {MONDAI_RANGE}")
        if not isinstance(value["choices"], list) or len(value["choices"]) != 4:
            raise ValueError(f"{qid}: choices must have exactly 4 items")
        if not isinstance(value["answer"], int) or not 1 <= value["answer"] <= 4:
            raise ValueError(f"{qid}: answer must be 1-4 (one-based)")

        underline = value.get("underline")
        if value["mondai"] in MONDAI_NEEDS_UNDERLINE and not underline:
            raise ValueError(f"{qid}: underline is required for mondai {value['mondai']}")
        if value["mondai"] == 3 and underline:
            raise ValueError(f"{qid}: mondai 3 (standalone word) must not have underline")

        return cls(
            id=qid,
            chapter=value["chapter"],
            kanji_range=value["kanji_range"],
            mondai=value["mondai"],
            no=value["no"],
            sentence=value["sentence"],
            underline=underline,
            choices=value["choices"],
            answer=value["answer"],
            explanation=value.get("explanation", ""),
        )
