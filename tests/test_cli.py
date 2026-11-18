"""End-to-end tests for the command-line interface."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from typing import List, Optional

import pytest

from jsonpeek import __version__
from jsonpeek.cli import EXIT_ERROR, EXIT_OK, main, run

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SAMPLE = os.path.join(DATA_DIR, "sample.json")

DOC = {
    "name": "jsonpeek",
    "version": "0.1.0",
    "count": 3,
    "tags": ["json", "cli", "query"],
    "author": {"name": "Ada", "email": "ada@example.com"},
    "users": [
        {"id": 1, "name": "Alice", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "editor"},
    ],
    "a.b": {"c": "dotted"},
}


def invoke(
    args: List[str],
    stdin_text: Optional[str] = None,
) -> "tuple[int, str, str]":
    """Run the CLI in-process and return ``(code, stdout, stderr)``."""
    out, err = io.StringIO(), io.StringIO()
    stdin = io.StringIO(stdin_text if stdin_text is not None else "")
    code = run(args, stdin=stdin, stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def write_json(tmp_path, value) -> str:
    path = tmp_path / "doc.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return str(path)


def test_simple_key_from_file(tmp_path):
    code, out, err = invoke(["name", write_json(tmp_path, DOC)])
    assert (code, err) == (EXIT_OK, "")
    assert out == '"jsonpeek"\n'


def test_nested_key_from_file(tmp_path):
    code, out, _ = invoke(["author.email", write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    assert out == '"ada@example.com"\n'


def test_array_index(tmp_path):
    code, out, _ = invoke(["users[1].name", write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    assert out == '"Bob"\n'


def test_wildcard_returns_list(tmp_path):
    code, out, _ = invoke(["users[*].id", write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    assert json.loads(out) == [1, 2]


def test_quoted_key(tmp_path):
    code, out, _ = invoke(['."a.b".c', write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    assert out == '"dotted"\n'


def test_root_prefix(tmp_path):
    code, out, _ = invoke(["$.tags[0]", write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    assert out == '"json"\n'


def test_raw_prints_bare_string(tmp_path):
    code, out, _ = invoke(["--raw", "author.name", write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    assert out == "Ada\n"


def test_raw_does_not_apply_to_objects(tmp_path):
    code, out, _ = invoke(["--raw", "author", write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    assert json.loads(out) == {"name": "Ada", "email": "ada@example.com"}


def test_compact_format(tmp_path):
    code, out, _ = invoke(["--format", "compact", "tags", write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    assert out == '["json","cli","query"]\n'


def test_jsonl_format(tmp_path):
    code, out, _ = invoke(["--format", "jsonl", "users[*]", write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    assert out.splitlines() == [
        '{"id":1,"name":"Alice","role":"admin"}',
        '{"id":2,"name":"Bob","role":"editor"}',
    ]


def test_table_format(tmp_path):
    code, out, _ = invoke(["--format", "table", "users[*]", write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    lines = out.splitlines()
    assert lines[0].split() == ["id", "name", "role"]
    assert set(lines[1]) <= {"-", " "}
    assert lines[2].startswith("1 ")
    assert "Alice" in lines[2]
    assert "editor" in lines[3]


def test_table_format_scalar_array(tmp_path):
    code, out, _ = invoke(["--format", "table", "tags", write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    assert out == "json\ncli\nquery\n"


def test_indent_option(tmp_path):
    code, out, _ = invoke(["--indent", "4", "author", write_json(tmp_path, DOC)])
    assert code == EXIT_OK
    assert out.splitlines()[1] == '    "name": "Ada",'


def test_reads_stdin_when_file_omitted():
    code, out, err = invoke(["users[0].name"], stdin_text=json.dumps(DOC))
    assert (code, err) == (EXIT_OK, "")
    assert out == '"Alice"\n'


def test_reads_stdin_with_dash():
    code, out, _ = invoke(["count", "-"], stdin_text=json.dumps(DOC))
    assert code == EXIT_OK
    assert out == "3\n"


def test_sample_fixture_file():
    code, out, _ = invoke(["users[*].name", SAMPLE])
    assert code == EXIT_OK
    assert json.loads(out) == ["Alice", "Bob", "Chen Wei"]


def test_missing_key_exits_two(tmp_path):
    code, out, err = invoke(["author.missing", write_json(tmp_path, DOC)])
    assert code == EXIT_ERROR
    assert out == ""
    assert "missing" in err
    assert err.startswith("jsonpeek: query failed:")


def test_index_out_of_range_exits_two(tmp_path):
    code, _, err = invoke(["tags[99]", write_json(tmp_path, DOC)])
    assert code == EXIT_ERROR
    assert "out of range" in err


def test_bad_json_exits_two(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"a": 1,,}', encoding="utf-8")
    code, out, err = invoke(["a", str(path)])
    assert code == EXIT_ERROR
    assert out == ""
    assert "invalid JSON" in err
    assert "line 1" in err


def test_empty_input_exits_two():
    code, _, err = invoke(["a"], stdin_text="   \n")
    assert code == EXIT_ERROR
    assert "empty" in err


def test_missing_file_exits_two(tmp_path):
    missing = str(tmp_path / "nope.json")
    code, _, err = invoke(["a", missing])
    assert code == EXIT_ERROR
    assert "cannot open" in err


def test_invalid_expression_exits_two(tmp_path):
    code, out, err = invoke(["a[", write_json(tmp_path, DOC)])
    assert code == EXIT_ERROR
    assert out == ""
    assert "invalid expression" in err


def test_negative_indent_exits_two(tmp_path):
    code, _, err = invoke(["--indent", "-1", "a", write_json(tmp_path, DOC)])
    assert code == EXIT_ERROR
    assert "--indent" in err


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as info:
        main(["--help"])
    assert info.value.code == 0
    captured = capsys.readouterr()
    assert "path expression" in captured.out
    assert "--format" in captured.out
    assert "users[*].name" in captured.out


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as info:
        main(["--version"])
    assert info.value.code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "jsonpeek {0}".format(__version__)


def test_module_entry_point_runs():
    result = subprocess.run(
        [sys.executable, "-m", "jsonpeek", "--version"],
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(DATA_DIR), "..", "src")),
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "jsonpeek {0}".format(__version__)
