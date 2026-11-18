"""Tests for the output renderers."""

from __future__ import annotations

import json

import pytest

from jsonpeek.output import display_width, dumps, pad, render, render_table


def test_pretty_default_indent_is_two():
    text = render({"a": 1, "b": [1, 2]})
    assert text == '{\n  "a": 1,\n  "b": [\n    1,\n    2\n  ]\n}'


def test_pretty_custom_indent():
    text = render({"a": 1}, indent=4)
    assert text == '{\n    "a": 1\n}'


def test_pretty_indent_zero():
    text = render({"a": 1}, indent=0)
    assert "\n" in text
    assert text.splitlines()[1].startswith('"a"')


def test_compact_has_no_whitespace():
    assert render({"a": 1, "b": [1, 2]}, fmt="compact") == '{"a":1,"b":[1,2]}'


def test_jsonl_expands_top_level_array():
    text = render([{"a": 1}, {"a": 2}], fmt="jsonl")
    assert text == '{"a":1}\n{"a":2}'


def test_jsonl_single_value():
    assert render({"a": 1}, fmt="jsonl") == '{"a":1}'
    assert render("hi", fmt="jsonl") == '"hi"'


def test_table_aligns_object_arrays():
    value = [{"id": 1, "name": "Alice"}, {"id": 22, "name": "Bo"}]
    lines = render_table(value).splitlines()
    assert lines[0] == "id  name"
    assert set(lines[1]) == {"-", " "}
    assert lines[2] == "1   Alice"
    assert lines[3] == "22  Bo"


def test_table_fills_missing_keys():
    value = [{"a": 1}, {"b": 2}]
    text = render_table(value)
    assert "\u2014" in text
    assert "a" in text and "b" in text


def test_table_scalar_array_one_row_each():
    assert render_table([1, "two", True]) == "1\ntwo\ntrue"


def test_table_nested_values_are_compact_json():
    text = render_table([{"a": {"b": 1}}])
    assert '{"b":1}' in text


def test_table_empty_array_is_empty_string():
    assert render_table([]) == ""


def test_table_non_array_falls_back_to_json():
    assert render_table({"a": 1}) == '{\n  "a": 1\n}'


def test_table_wide_characters_align():
    value = [{"k": "\u6570\u636e", "n": 1}, {"k": "ab", "n": 2}]
    lines = render_table(value).splitlines()
    # The first column is padded to the widest cell, counting CJK as 2 columns.
    assert lines[2].startswith("\u6570\u636e  1")
    assert lines[3].startswith("ab    2")


def test_raw_string_is_verbatim():
    assert render("line1\nline2", raw=True) == "line1\nline2"
    assert render("hi", raw=True) == "hi"


def test_raw_ignored_for_non_strings():
    assert render({"a": 1}, raw=True) == dumps({"a": 1})


def test_unknown_format_raises():
    with pytest.raises(ValueError):
        render({"a": 1}, fmt="yaml")


def test_unicode_is_not_escaped():
    assert dumps({"k": "\u6570\u636e"}, compact=True) == '{"k":"\u6570\u636e"}'


def test_pad_and_width_helpers():
    assert display_width("ab") == 2
    assert display_width("\u6570\u636e") == 4
    assert pad("ab", 4) == "ab  "
    assert pad("abcd", 2) == "abcd"


def test_dumps_roundtrip():
    value = {"a": [1, 2, {"b": None}], "c": True}
    assert json.loads(dumps(value)) == value
