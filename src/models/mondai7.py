from dataclasses import dataclass


@dataclass(frozen=True)
class Mondai7Question:
    id: str
    period: str
    no: int
    question: str
    choices: list[str]
    answer: int
    explanation: str

    @classmethod
    def from_dict(cls, value: dict) -> "Mondai7Question":
        question_id = str(value.get("id", "<missing id>"))
        required = ("id", "no", "question", "choices", "answer", "explanation")
        missing = [key for key in required if key not in value]
        if missing:
            raise ValueError(f"{question_id}: missing {', '.join(missing)}")
        choices = value["choices"]
        if not isinstance(choices, list) or len(choices) != 4:
            raise ValueError(f"{question_id}: choices must contain exactly 4 entries")
        if value["answer"] not in range(1, 5):
            raise ValueError(f"{question_id}: answer must be in 1..4")
        return cls(
            id=value["id"],
            period=value.get("period", ""),
            no=value["no"],
            question=value["question"],
            choices=value["choices"],
            answer=value["answer"],
            explanation=value["explanation"],
        )
