import html

import genanki


def escaped(value: object) -> str:
    return html.escape(str(value), quote=False).replace("\n", "<br>")


def tags(mondai: int, period: str) -> list[str]:
    return ["JLPT", "N2", "Grammar", f"Mondai{mondai}", period.replace(".", "_")]


def kanji_group(mondai: int) -> str:
    """Map the four Kanji question types to their three study skills."""
    if mondai == 1:
        return "doc_trong_cau"
    if mondai == 3:
        return "doc_tu_don"
    if mondai in (2, 4):
        return "viet_kanji"
    raise ValueError(f"unknown Kanji mondai: {mondai}")


def kanji_tags(chapter: int, mondai: int, kanji_range: str) -> list[str]:
    """Tags shared by deck selection and Kanji note creation."""
    return [f"chapter{chapter}", f"mondai{mondai}", kanji_group(mondai)]


def note_with_guid(model: genanki.Model, fields: list[str], note_tags: list[str], question_id: str) -> genanki.Note:
    note = genanki.Note(model=model, fields=fields, tags=note_tags)
    note.guid = genanki.guid_for(question_id)
    return note
