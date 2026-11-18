"""Rendering helpers for :mod:`jsonpeek`.

Every function here turns an already-evaluated Python object into the text that
the CLI writes to stdout.  Rendering never mutates the value and never raises on
odd JSON shapes -- it degrades to plain ``json.dumps`` instead.
"""

from __future__ import annotations

import json
import unicodedata
from typing import Any, List, Sequence

__all__ = [
    "FORMATS",
    "dumps",
    "render",
    "render_table",
    "display_width",
    "pad",
]

FORMATS = ("pretty", "compact", "jsonl", "table")

_MISSING = "\u2014"  # em dash used for absent object keys inside a table


def dumps(value: Any, indent: int = 2, compact: bool = False) -> str:
    """Serialize *value* as JSON text.

    ``compact`` produces single-line output with ``", "``/``": "`` separators,
    otherwise the text is indented by *indent* spaces.
    """
    if compact:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(value, ensure_ascii=False, indent=indent)


def render(
    value: Any,
    fmt: str = "pretty",
    indent: int = 2,
    raw: bool = False,
) -> str:
    """Render *value* in the requested output *fmt*.

    :param value: the evaluated JSON value.
    :param fmt: one of ``pretty``, ``compact``, ``jsonl`` or ``table``.
    :param indent: indentation width used by the ``pretty`` format.
    :param raw: when ``True`` and the value is a string, return it verbatim.
    """
    if fmt not in FORMATS:
        raise ValueError("unknown format: {0!r}".format(fmt))

    if raw and isinstance(value, str):
        return value

    if fmt == "pretty":
        return dumps(value, indent=indent)
    if fmt == "compact":
        return dumps(value, compact=True)
    if fmt == "jsonl":
        return render_jsonl(value)
    return render_table(value, indent=indent)


def render_jsonl(value: Any) -> str:
    """Render one JSON value per line.

    A top-level array is expanded into one line per element; anything else
    becomes a single line.
    """
    if isinstance(value, list):
        return "\n".join(dumps(item, compact=True) for item in value)
    return dumps(value, compact=True)


def _scalar_cell(value: Any) -> str:
    """Render a table cell: strings stay bare, everything else is JSON."""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return dumps(value, compact=True)
    return json.dumps(value, ensure_ascii=False)


def render_table(value: Any, indent: int = 2) -> str:
    """Render an array of objects as an aligned table.

    * an array of objects with at least one shared key becomes a table whose
      columns are the union of keys, in first-seen order;
    * an array of scalars (or of mixed non-object values) is printed one row
      per element, without a header;
    * a non-array value falls back to compact JSON.
    """
    if not isinstance(value, list):
        return dumps(value, indent=indent)

    if not value:
        return ""

    if not all(isinstance(item, dict) for item in value):
        return "\n".join(_scalar_cell(item) for item in value)

    columns: List[str] = []
    for item in value:
        for key in item:
            if key not in columns:
                columns.append(key)

    if not columns:
        return "\n".join("{}" for _ in value)

    rows: List[List[str]] = []
    for item in value:
        rows.append(
            [_scalar_cell(item[key]) if key in item else _MISSING for key in columns]
        )

    widths = [display_width(name) for name in columns]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], display_width(cell))

    lines = [_join_row(columns, widths), _join_rule(widths)]
    lines.extend(_join_row(row, widths) for row in rows)
    return "\n".join(line.rstrip() for line in lines)


def _join_row(cells: Sequence[str], widths: Sequence[int]) -> str:
    return "  ".join(pad(cell, width) for cell, width in zip(cells, widths))


def _join_rule(widths: Sequence[int]) -> str:
    return "  ".join("-" * width for width in widths)


def display_width(text: str) -> int:
    """Return the terminal column width of *text*.

    East-Asian wide and fullwidth characters count as two columns so that
    mixed CJK/ASCII tables stay aligned.
    """
    width = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def pad(text: str, width: int) -> str:
    """Left-align *text* inside *width* display columns."""
    return text + " " * max(0, width - display_width(text))
