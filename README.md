# JLPT N2 Grammar Anki Generator

Build a self-contained Anki package for JLPT N2 grammar exercises using Python and `genanki`.

The generated package contains three permanent subdecks:

- `JLPT N2 Grammar::Mondai 7` — multiple-choice questions
- `JLPT N2 Grammar::Mondai 8` — sentence reconstruction / ordering questions
- `JLPT N2 Grammar::Mondai 9` — context cloze questions with four choices per blank

The current dataset contains 95 Mondai 8 questions. Mondai 7 and Mondai 9 are created even when their data files are empty.

## Requirements

- Python 3.10 or later
- `genanki` (installed from `requirements.txt`)

## Setup

Create and activate a virtual environment:

```cmd  
python -m venv venv
venv\Scripts\activate.bat
```

Install dependencies:

```cmd
python -m pip install -r requirements.txt
```

## Build the Anki package

```cmd
python -m src.main
```

The output is written to:

```text
output/JLPT_N2_Grammar.apkg
```

Import that `.apkg` file into Anki. Its templates are embedded in the package, so reviewing cards does not require an internet connection.

## Run tests

```cmd
python -m unittest discover -s tests -v
```

## Data files

Add or replace data only in these files:

```text
data/mondai7/questions.json
data/mondai8/questions.json
data/mondai9/questions.json
```

Do not modify the generator, models, or templates when adding questions that follow the schemas below.

### Mondai 7: Multiple Choice

```json
{
  "id": "N2-M7-2020.07-01",
  "period": "2020.07",
  "no": 1,
  "question": "Question text",
  "choices": ["Option A", "Option B", "Option C", "Option D"],
  "answer": 2,
  "explanation": "Explanation text"
}
```

`answer` is one-based: `1` means A, `2` means B, and so on.

### Mondai 8: Ordering

```json
{
  "index": 1,
  "period": "2020.07",
  "no": 1,
  "sentence_all_blanked": "Sentence __ __ ★ __.",
  "choices": {"1": "A", "2": "B", "3": "C", "4": "D"},
  "answer_order": "2341",
  "star_position_in_blanks": 3,
  "star_choice_number": 4,
  "full_sentence": "Completed sentence."
}
```

`answer_order` must be a permutation of `1234`. The note ID is derived stably from the period and question number, for example `N2-M8-2020.07-1`.

### Mondai 9: Context Cloze

```json
{
  "id": "N2-M9-2020.07-01",
  "period": "2020.07",
  "no": 1,
  "context": "A context with four blanks.",
  "questions": [
    {"id": "1", "choices": ["A", "B", "C", "D"], "answer": 1},
    {"id": "2", "choices": ["A", "B", "C", "D"], "answer": 2},
    {"id": "3", "choices": ["A", "B", "C", "D"], "answer": 3},
    {"id": "4", "choices": ["A", "B", "C", "D"], "answer": 4}
  ]
}
```

One context object always becomes one Anki note.

## Validation and stable identities

The build validates every record and reports the affected question ID when data is invalid. Each Anki note uses a deterministic GUID based on its source ID, so rebuilding the package does not change card identity when data is reordered.
