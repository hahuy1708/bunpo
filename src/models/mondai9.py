from dataclasses import dataclass


@dataclass(frozen=True)
class Mondai9Subquestion:
    id: str
    choices: list[str]
    answer: int


@dataclass(frozen=True)
class Mondai9Question:
    id: str
    period: str
    no: int
    context: str
    questions: list[Mondai9Subquestion]

    @classmethod
    def from_dict(cls, value: dict) -> "Mondai9Question":
        question_id = str(value.get("id", "<missing id>"))
        required = ("id", "period", "no", "context", "questions")
        missing = [key for key in required if key not in value]
        if missing:
            raise ValueError(f"{question_id}: missing {', '.join(missing)}")
        raw_questions = value["questions"]
        if not isinstance(raw_questions, list) or len(raw_questions) != 4:
            raise ValueError(f"{question_id}: questions must contain exactly 4 entries")
        questions = []
        for position, subquestion in enumerate(raw_questions, start=1):
            choices = subquestion.get("choices", [])
            if not isinstance(choices, list) or len(choices) != 4:
                raise ValueError(f"{question_id}: question {position} must have exactly 4 choices")
            if subquestion.get("answer") not in range(1, 5):
                raise ValueError(f"{question_id}: question {position} answer must be in 1..4")
            if "id" not in subquestion:
                raise ValueError(f"{question_id}: question {position} is missing id")
            questions.append(Mondai9Subquestion(subquestion["id"], choices, subquestion["answer"]))
        return cls(value["id"], value["period"], value["no"], value["context"], questions)
