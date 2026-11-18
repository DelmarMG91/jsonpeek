"""Tests for the expression tokenizer and evaluator."""

from __future__ import annotations

import pytest

from jsonpeek.query import (
    PathStep,
    QueryIndexError,
    QueryKeyError,
    QuerySyntaxError,
    QueryTypeError,
    evaluate,
    query,
    tokenize,
)

DOC = {
    "name": "jsonpeek",
    "version": "0.1.0",
    "author": {"name": "Ada", "links": {"home": "https://example.com"}},
    "tags": ["json", "cli", "query"],
    "users": [
        {"id": 1, "name": "Alice", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "editor"},
        {"id": 3, "name": "Chen", "role": "viewer"},
    ],
    "a.b": {"c": "dotted"},
    "matrix": [[1, 2], [3, 4]],
}


def test_simple_key():
    assert query(DOC, "name") == "jsonpeek"


def test_nested_keys():
    assert query(DOC, "author.links.home") == "https://example.com"


def test_array_index():
    assert query(DOC, "users[0].name") == "Alice"
    assert query(DOC, "tags[2]") == "query"


def test_negative_index():
    assert query(DOC, "tags[-1]") == "query"
    assert query(DOC, "users[-1].role") == "viewer"


def test_wildcard_projection():
    assert query(DOC, "users[*].name") == ["Alice", "Bob", "Chen"]
    assert query(DOC, "tags[*]") == ["json", "cli", "query"]


def test_wildcard_on_object_returns_values():
    assert query(DOC, "author[*]") == ["Ada", {"home": "https://example.com"}]


def test_chained_index_steps():
    assert query(DOC, "matrix[1][0]") == 3
    assert query(DOC, "matrix[0][1]") == 2


def test_quoted_key():
    assert query(DOC, '."a.b".c') == "dotted"
    assert query(DOC, '["a.b"]["c"]') == "dotted"


def test_root_prefix():
    assert query(DOC, "$.name") == "jsonpeek"
    assert query(DOC, "$.users[0].id") == 1
    assert query(DOC, "@.tags[0]") == "json"


def test_tokenize_shapes():
    assert tokenize("a.b") == [PathStep("key", "a"), PathStep("key", "b")]
    assert tokenize("a[0]") == [PathStep("key", "a"), PathStep("index", 0)]
    assert tokenize("a[*]") == [PathStep("key", "a"), PathStep("wildcard")]
    assert tokenize('."x.y"') == [PathStep("key", "x.y")]
    assert tokenize("$") == []


def test_missing_key_raises():
    with pytest.raises(QueryKeyError) as info:
        query(DOC, "author.missing")
    assert "missing" in str(info.value)
    assert "$.author" in str(info.value)


def test_index_out_of_range_raises():
    with pytest.raises(QueryIndexError) as info:
        query(DOC, "tags[9]")
    assert "out of range" in str(info.value)


def test_wrong_type_raises():
    with pytest.raises(QueryTypeError):
        query(DOC, "name.first")
    with pytest.raises(QueryTypeError):
        query(DOC, "name[0]")
    with pytest.raises(QueryTypeError):
        query(DOC, "name[*]")


@pytest.mark.parametrize(
    "expression",
    ["", "   ", ".", "a.", "a[", "a[0", "a[x]", "a[*", '."unterminated', "$x", "a]b"],
)
def test_invalid_expression_raises(expression):
    with pytest.raises(QuerySyntaxError):
        tokenize(expression)


def test_expression_is_stripped():
    assert query(DOC, "  author.name  ") == "Ada"


def test_wildcard_tolerates_missing_members():
    assert query(DOC, "users[*].missing") == [None, None, None]


def test_evaluate_accepts_prebuilt_steps():
    steps = tokenize("users[1].name")
    assert evaluate(DOC, steps) == "Bob"
