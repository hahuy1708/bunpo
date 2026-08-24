from dataclasses import dataclass


@dataclass(frozen=True)
class Mondai8Question:
    index: int
    period: str
    no: int
    sentence_all_blanked: str
    choices: dict[str, str]
    answer_order: str
    star_position_in_blanks: int
    star_choice_number: int
    full_sentence: str
    explanation: str = ""

    @property
    def id(self) -> str:
        return f"N2-M8-{self.period}-{self.no}"

    @classmethod
    def from_dict(cls, value: dict) -> "Mondai8Question":
        question_id = f"N2-M8-{value.get('period', '?')}-{value.get('no', '?')}"
        required = ("index", "sentence_all_blanked", "choices", "answer_order", "star_position_in_blanks", "star_choice_number", "full_sentence")
        missing = [key for key in required if key not in value]
        if missing:
            raise ValueError(f"{question_id}: missing {', '.join(missing)}")
        choices = value["choices"]
        if not isinstance(choices, dict) or set(choices) != {"1", "2", "3", "4"}:
            raise ValueError(f"{question_id}: choices must have keys 1, 2, 3, 4")
        if sorted(str(value["answer_order"])) != ["1", "2", "3", "4"]:
            raise ValueError(f"{question_id}: answer_order must be a permutation of 1234")
        for key in ("star_choice_number", "star_position_in_blanks"):
            if value[key] not in range(1, 5):
                raise ValueError(f"{question_id}: {key} must be in 1..4")
        if not str(value["full_sentence"]).strip():
            raise ValueError(f"{question_id}: full_sentence is required")
        return cls(
            index=value["index"],
            period=value.get("period", "?"),
            no=value.get("no", 0),
            sentence_all_blanked=value["sentence_all_blanked"],
            choices=choices,
            answer_order=value["answer_order"],
            star_position_in_blanks=value["star_position_in_blanks"],
            star_choice_number=value["star_choice_number"],
            full_sentence=value["full_sentence"],
            explanation=value.get("explanation", ""),
        )
