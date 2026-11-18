"""Expression parser and evaluator for :mod:`jsonpeek`.

The expression language is a deliberately small subset of JSONPath::

    a.b.c              nested keys
    users[0].name      array index (negative indices count from the end)
    users[*].name      wildcard projection over an array or object
    ."a.b".c           quoted key, for names containing dots or spaces
    $.users[*].id      optional ``$`` (or ``@``) root prefix

The module is dependency free: the tokenizer and the evaluator are both
implemented here on top of the standard library only.
"""

from __future__ import annotations

from typing import Any, List, Sequence, Tuple

__all__ = [
    "PathStep",
    "QueryError",
    "QuerySyntaxError",
    "QueryKeyError",
    "QueryIndexError",
    "QueryTypeError",
    "tokenize",
    "evaluate",
    "query",
]

# Characters that end a bare (unquoted) key name.
_BARE_KEY_STOP = ".[]\"' \t\r\n"
_ROOT_PREFIXES = ("$", "@")


class QueryError(Exception):
    """Base class for every error raised while parsing or evaluating."""


class QuerySyntaxError(QueryError):
    """The expression could not be tokenized."""


class QueryKeyError(QueryError):
    """A key was not present in an object."""


class QueryIndexError(QueryError):
    """An array index was outside the bounds of the array."""


class QueryTypeError(QueryError):
    """A step was applied to a value of the wrong JSON type."""


class PathStep:
    """One step of a parsed expression.

    ``kind`` is one of ``"key"``, ``"index"`` or ``"wildcard"``.  ``value``
    holds the key name (``str``) or the index (``int``) and is ``None`` for a
    wildcard.
    """

    __slots__ = ("kind", "value")

    def __init__(self, kind: str, value: Any = None) -> None:
        if kind not in ("key", "index", "wildcard"):
            raise ValueError("invalid step kind: {0!r}".format(kind))
        self.kind = kind
        self.value = value

    # -- rendering ---------------------------------------------------------
    def render(self) -> str:
        """Return the canonical expression text for this step."""
        if self.kind == "key":
            name = str(self.value)
            if _is_bare_key(name):
                return "." + name
            return '["{0}"]'.format(name.replace("\\", "\\\\").replace('"', '\\"'))
        if self.kind == "index":
            return "[{0}]".format(self.value)
        return "[*]"

    # -- dunder ------------------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PathStep):
            return NotImplemented
        return (self.kind, self.value) == (other.kind, other.value)

    def __hash__(self) -> int:
        return hash((self.kind, self.value))

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return "PathStep({0!r}, {1!r})".format(self.kind, self.value)


def _is_bare_key(name: str) -> bool:
    """Return ``True`` when *name* can be written without quotes."""
    if not name:
        return False
    return not any(ch in _BARE_KEY_STOP for ch in name)


def _read_quoted(text: str, pos: int) -> Tuple[str, int]:
    """Read a double-quoted key starting at ``text[pos] == '"'``.

    Returns the unescaped key and the position just past the closing quote.
    """
    assert text[pos] == '"'
    pos += 1
    out: List[str] = []
    while pos < len(text):
        ch = text[pos]
        if ch == "\\":
            pos += 1
            if pos >= len(text):
                raise QuerySyntaxError("unterminated escape sequence in quoted key")
            esc = text[pos]
            out.append({"n": "\n", "t": "\t", "r": "\r"}.get(esc, esc))
            pos += 1
        elif ch == '"':
            return "".join(out), pos + 1
        else:
            out.append(ch)
            pos += 1
    raise QuerySyntaxError("unterminated quoted key")


def tokenize(expression: str) -> List[PathStep]:
    """Split *expression* into a list of :class:`PathStep` objects.

    Raises :class:`QuerySyntaxError` when the expression is empty or malformed.
    """
    if expression is None:
        raise QuerySyntaxError("expression is empty")
    text = expression.strip()
    if not text:
        raise QuerySyntaxError("expression is empty")

    steps: List[PathStep] = []
    pos = 0

    if text[0] in _ROOT_PREFIXES:
        pos = 1
        if pos < len(text) and text[pos] not in ".[":
            raise QuerySyntaxError(
                "unexpected character {0!r} after {1!r} at position {2}".format(
                    text[pos], text[0], pos
                )
            )

    at_start = True
    while pos < len(text):
        ch = text[pos]

        if ch == ".":
            pos += 1
            if pos >= len(text):
                raise QuerySyntaxError("expected a key name after '.'")
            if text[pos] == '"':
                name, pos = _read_quoted(text, pos)
                steps.append(PathStep("key", name))
            else:
                start = pos
                while pos < len(text) and text[pos] not in _BARE_KEY_STOP:
                    pos += 1
                name = text[start:pos]
                if not name:
                    raise QuerySyntaxError(
                        "expected a key name at position {0}".format(start)
                    )
                steps.append(PathStep("key", name))

        elif ch == "[":
            step, pos = _read_bracket(text, pos)
            steps.append(step)

        elif ch == '"':
            name, pos = _read_quoted(text, pos)
            steps.append(PathStep("key", name))

        elif at_start and ch not in _BARE_KEY_STOP:
            start = pos
            while pos < len(text) and text[pos] not in _BARE_KEY_STOP:
                pos += 1
            steps.append(PathStep("key", text[start:pos]))

        else:
            raise QuerySyntaxError(
                "unexpected character {0!r} at position {1}".format(ch, pos)
            )

        at_start = False

    return steps


def _read_bracket(text: str, pos: int) -> Tuple[PathStep, int]:
    """Parse one ``[...]`` segment starting at ``text[pos] == '['``."""
    open_pos = pos
    pos += 1
    if pos >= len(text):
        raise QuerySyntaxError("unclosed '[' at position {0}".format(open_pos))

    ch = text[pos]

    if ch == "*":
        pos += 1
        if pos >= len(text) or text[pos] != "]":
            raise QuerySyntaxError("expected ']' after '*' at position {0}".format(pos))
        return PathStep("wildcard"), pos + 1

    if ch == "]":
        # ``[]`` is accepted as an alias for ``[*]``.
        return PathStep("wildcard"), pos + 1

    if ch == '"':
        name, pos = _read_quoted(text, pos)
        if pos >= len(text) or text[pos] != "]":
            raise QuerySyntaxError(
                "expected ']' after quoted key at position {0}".format(pos)
            )
        return PathStep("key", name), pos + 1

    start = pos
    if ch == "-":
        pos += 1
    while pos < len(text) and text[pos].isdigit():
        pos += 1
    digits = text[start:pos]
    if not digits or digits == "-":
        raise QuerySyntaxError(
            "expected an integer index at position {0}".format(start)
        )
    if pos >= len(text) or text[pos] != "]":
        raise QuerySyntaxError("expected ']' at position {0}".format(pos))
    return PathStep("index", int(digits)), pos + 1


def evaluate(document: Any, steps: Sequence[PathStep]) -> Any:
    """Apply *steps* to *document* and return the selected value.

    A path without a wildcard yields the single selected value; a path that
    contains at least one wildcard yields a list of every match, in document
    order (an empty list when nothing matched).

    Inside a wildcard projection a missing key or out-of-range index yields
    ``None`` instead of an error, which keeps projections over heterogeneous
    arrays usable.  Outside a projection the first failure raises.
    """
    nodes: List[Tuple[Any, str]] = [(document, "$")]
    projected = False

    for step in steps:
        selected: List[Tuple[Any, str]] = []

        for node, path in nodes:
            if step.kind == "key":
                name = str(step.value)
                if isinstance(node, dict):
                    if name in node:
                        selected.append((node[name], path + PathStep("key", name).render()))
                    elif projected:
                        selected.append((None, path + PathStep("key", name).render()))
                    else:
                        raise QueryKeyError(
                            "key {0!r} not found at {1}".format(name, path)
                        )
                elif projected:
                    selected.append((None, path + PathStep("key", name).render()))
                else:
                    raise QueryTypeError(
                        "cannot read key {0!r} from {1} at {2}".format(
                            name, _json_type(node), path
                        )
                    )

            elif step.kind == "index":
                index = int(step.value)
                if isinstance(node, list):
                    real = index if index >= 0 else len(node) + index
                    if 0 <= real < len(node):
                        selected.append((node[real], path + "[{0}]".format(index)))
                    elif projected:
                        selected.append((None, path + "[{0}]".format(index)))
                    else:
                        raise QueryIndexError(
                            "index {0} out of range at {1} (length {2})".format(
                                index, path, len(node)
                            )
                        )
                elif projected:
                    selected.append((None, path + "[{0}]".format(index)))
                else:
                    raise QueryTypeError(
                        "cannot index {0} at {1} with [{2}]".format(
                            _json_type(node), path, index
                        )
                    )

            else:  # wildcard
                projected = True
                child_path = path + "[*]"
                if isinstance(node, list):
                    for item in node:
                        selected.append((item, child_path))
                elif isinstance(node, dict):
                    for item in node.values():
                        selected.append((item, child_path))
                else:
                    raise QueryTypeError(
                        "cannot iterate over {0} at {1}".format(
                            _json_type(node), path
                        )
                    )

        nodes = selected

    if projected:
        return [node for node, _ in nodes]
    if not nodes:  # pragma: no cover - defensive, unreachable for valid paths
        raise QueryError("expression selected nothing")
    return nodes[0][0]


def _json_type(value: Any) -> str:
    """Return the JSON type name of *value*."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def query(document: Any, expression: str) -> Any:
    """Parse *expression* and evaluate it against *document*."""
    return evaluate(document, tokenize(expression))
