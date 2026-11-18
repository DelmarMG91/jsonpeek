"""Command-line interface for :mod:`jsonpeek`."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, List, Optional, Sequence, TextIO

from . import __version__
from .output import FORMATS, render
from .query import QueryError, evaluate, tokenize

__all__ = ["main", "build_parser", "load_document", "run"]

EXIT_OK = 0
EXIT_ERROR = 2

_DESCRIPTION = """\
Read JSON from a file or stdin, evaluate a small path expression against it,
and print the result.  Zero dependencies, one job.
"""

_EPILOG = """\
expression syntax:
  a.b.c              nested keys
  users[0].name      array index (negative indices count from the end)
  users[*].name      wildcard over an array or object (returns a list)
  ."a.b".c           quoted key for names containing dots or spaces
  $.users[*].id      optional '$' (or '@') root prefix

examples:
  jsonpeek users[0].name data.json
  jsonpeek 'users[*].email' data.json --raw
  cat data.json | jsonpeek '$.items[*]' --format table
"""


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser used by :func:`main`."""
    parser = argparse.ArgumentParser(
        prog="jsonpeek",
        description=_DESCRIPTION,
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "expr",
        metavar="EXPR",
        help="path expression to evaluate, e.g. 'users[0].name' or 'users[*].id'",
    )
    parser.add_argument(
        "file",
        metavar="FILE",
        nargs="?",
        default="-",
        help="JSON file to read; omit or use '-' to read stdin",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="print a selected string without JSON quotes or escapes",
    )
    parser.add_argument(
        "--format",
        dest="format",
        choices=FORMATS,
        default="pretty",
        help="output format (default: pretty)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        metavar="N",
        help="indentation width for the pretty format (default: 2)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="jsonpeek {0}".format(__version__),
        help="print the version and exit",
    )
    return parser


def load_document(stream: TextIO, source: str) -> Any:
    """Parse JSON from *stream*, raising ``ValueError`` with a readable message."""
    try:
        text = stream.read()
    except OSError as exc:
        raise ValueError("cannot read {0}: {1}".format(source, exc)) from exc

    if not text.strip():
        raise ValueError("{0} is empty".format(source))

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "invalid JSON in {0} at line {1} column {2}: {3}".format(
                source, exc.lineno, exc.colno, exc.msg
            )
        ) from exc


def run(
    argv: Optional[Sequence[str]] = None,
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> int:
    """Execute one CLI invocation and return its exit code.

    This is the testable core of :func:`main`; it never calls ``sys.exit``.
    """
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.indent < 0:
        print("jsonpeek: error: --indent must be >= 0", file=stderr)
        return EXIT_ERROR

    try:
        steps = tokenize(args.expr)
    except QueryError as exc:
        print("jsonpeek: invalid expression: {0}".format(exc), file=stderr)
        return EXIT_ERROR

    if args.file in (None, "-"):
        source = "<stdin>"
        try:
            document = load_document(stdin, source)
        except ValueError as exc:
            print("jsonpeek: error: {0}".format(exc), file=stderr)
            return EXIT_ERROR
    else:
        source = args.file
        try:
            with open(args.file, "r", encoding="utf-8") as handle:
                document = load_document(handle, source)
        except OSError as exc:
            print(
                "jsonpeek: error: cannot open {0}: {1}".format(
                    source, exc.strerror or exc
                ),
                file=stderr,
            )
            return EXIT_ERROR
        except ValueError as exc:
            print("jsonpeek: error: {0}".format(exc), file=stderr)
            return EXIT_ERROR

    try:
        value = evaluate(document, steps)
    except QueryError as exc:
        print("jsonpeek: query failed: {0}".format(exc), file=stderr)
        return EXIT_ERROR

    text = render(value, fmt=args.format, indent=args.indent, raw=args.raw)
    if text:
        stdout.write(text)
        stdout.write("\n")
    stdout.flush()
    return EXIT_OK


def main(argv: Optional[List[str]] = None) -> int:
    """Console-script entry point."""
    try:
        return run(argv)
    except BrokenPipeError:  # pragma: no cover - depends on downstream pipe
        return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
