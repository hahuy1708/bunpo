import html

import genanki


def escaped(value: object) -> str:
    return html.escape(str(value), quote=False).replace("\n", "<br>")


def tags(mondai: int, period: str) -> list[str]:
    return ["JLPT", "N2", "Grammar", f"Mondai{mondai}", period.replace(".", "_")]


def note_with_guid(model: genanki.Model, fields: list[str], note_tags: list[str], question_id: str) -> genanki.Note:
    note = genanki.Note(model=model, fields=fields, tags=note_tags)
    note.guid = genanki.guid_for(question_id)
    return note
