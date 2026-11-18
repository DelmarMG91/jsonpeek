# jsonpeek

> A tiny, zero-dependency command-line JSON query tool — a lean alternative to `jq` for the 90% of queries you actually type.

[![CI](https://github.com/DelmarMG91/jsonpeek/actions/workflows/ci.yml/badge.svg)](https://github.com/DelmarMG91/jsonpeek/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/pypi-v0.1.0-orange.svg)](https://pypi.org/project/jsonpeek/)

`jsonpeek` reads JSON from a file or standard input, evaluates a small path
expression against it, and prints the result. No filter language, no DSL to
learn, no dependencies to install — just paths.

```console
$ jsonpeek 'users[*].name' examples/users.json
[
  "Alice",
  "Bob",
  "Chen Wei"
]
```

## Features

- **Zero dependencies.** Standard library only, one small package, installs in a second.
- **Readable paths.** `a.b.c`, `users[0].name`, `users[*].name`, `."a.b".c` — that is the whole grammar.
- **Optional root prefix.** Write `$.users[*].id` if you like JSONPath muscle memory; `$` and `@` are both accepted and ignored.
- **Four output formats.** `pretty` (default), `compact`, `jsonl`, and `table` for quick eyeballing of record arrays.
- **`--raw` for shell pipelines.** Emit a selected string without quotes so it can be piped straight into another command.
- **Honest errors.** Missing keys, out-of-range indices and malformed JSON produce a clear message on stderr and exit code `2`.
- **CJK-aware tables.** Wide characters count as two columns, so mixed ASCII/CJK tables stay aligned.
- **Tested.** 72 pytest cases across the tokenizer, evaluator, renderers and CLI.

## Install

From a checkout:

```console
$ git clone https://github.com/DelmarMG91/jsonpeek.git
$ cd jsonpeek
$ python -m pip install .
```

Editable install with the test extras:

```console
$ python -m pip install -e ".[dev]"
```

Run without installing at all:

```console
$ PYTHONPATH=src python -m jsonpeek --version
jsonpeek 0.1.0
```

## Quick Start

Given `examples/users.json`:

```json
{
  "name": "jsonpeek",
  "version": "0.1.0",
  "stars": 1280,
  "author": {
    "name": "Ada Lovelace",
    "email": "ada@example.com"
  },
  "users": [
    { "id": 1, "name": "Alice", "role": "admin", "active": true },
    { "id": 2, "name": "Bob", "role": "editor", "active": false },
    { "id": 3, "name": "Chen Wei", "role": "viewer", "active": true }
  ],
  "a.b": { "c": "dotted" }
}
```

Pick a single value:

```console
$ jsonpeek 'users[0].name' examples/users.json
"Alice"
```

Drop the JSON quoting when you want to use the value in a shell pipeline:

```console
$ jsonpeek --raw 'users[0].name' examples/users.json
Alice
```

Project a field across an array — a wildcard always returns a list:

```console
$ jsonpeek 'users[*].name' examples/users.json
[
  "Alice",
  "Bob",
  "Chen Wei"
]
```

Render records as a table:

```console
$ jsonpeek --format table 'users[*]' examples/users.json
id  name      role    active
--  --------  ------  ------
1   Alice     admin   true
2   Bob       editor  false
3   Chen Wei  viewer  true
```

Read from stdin by omitting the file (or passing `-`):

```console
$ curl -s https://api.example.com/users | jsonpeek '$.users[*].id' --format jsonl
1
2
3
```

Keys containing dots need quotes:

```console
$ jsonpeek '."a.b".c' examples/users.json
"dotted"
```

Failures are explicit:

```console
$ jsonpeek 'users[9].name' examples/users.json
jsonpeek: query failed: index 9 out of range at $.users (length 3)
$ echo "exit=$?"
exit=2
```

## Expression Syntax

| Expression | Meaning |
| --- | --- |
| `name` | Top-level key. |
| `author.name` | Nested key. |
| `users[0].name` | First element of an array, then a key. |
| `users[-1].name` | Negative indices count from the end. |
| `matrix[1][0]` | Chained indices into nested arrays. |
| `users[*].name` | Wildcard projection; always returns a list. |
| `users[*]` | The array itself, element by element. |
| `author[*]` | Wildcard over an object yields its values. |
| `."a.b".c` | Quoted key, for names containing dots or spaces. |
| `["a.b"]["c"]` | Bracket form of the same thing. |
| `$.users[0].id` | Optional `$` (or `@`) root prefix. |

Notes:

- A path containing at least one `[*]` returns a **list** of every match; a path
  without a wildcard returns the single selected value.
- Inside a wildcard projection, a missing key or out-of-range index yields `null`
  instead of failing, so projections over heterogeneous records stay usable.
  Outside a projection the first failure is an error.
- Keys made only of `A-Z a-z 0-9 _ -` can be written bare; anything else should be
  quoted.
- There is no filter, arithmetic, slicing or function syntax. `jsonpeek` selects,
  it does not compute.

## Options

| Option | Default | Description |
| --- | --- | --- |
| `EXPR` | *(required)* | Path expression to evaluate. |
| `FILE` | `-` (stdin) | JSON file to read. Omit it, or pass `-`, to read standard input. |
| `--raw` | off | Print a selected string verbatim — no quotes, no escaping. Ignored for non-strings. |
| `--format {pretty,compact,jsonl,table}` | `pretty` | Output format. See below. |
| `--indent N` | `2` | Indentation width for the `pretty` format. `0` puts every key on its own line. |
| `--version` | — | Print `jsonpeek 0.1.0` and exit. |
| `-h`, `--help` | — | Show usage, the expression grammar and examples. |

### Output formats

| Format | Behavior |
| --- | --- |
| `pretty` | Indented JSON, `--indent` spaces (default 2). |
| `compact` | Single line, no spaces: `{"a":1}`. |
| `jsonl` | One JSON value per line; a top-level array is expanded, one line per element. |
| `table` | An array of objects becomes an aligned table (union of keys, first-seen order, `—` for absent cells). An array of scalars becomes one row per element. A non-array falls back to `pretty`. |

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Query succeeded and output was written. |
| `2` | Invalid expression, unreadable file, malformed/empty JSON, or a failed lookup. A message is written to stderr. |

## Compared with other tools

`jq` is a full filter language and the right answer for complex transformations;
`jsonpeek` trades that power for a grammar you can hold in your head and a
dependency-free install that works on any Python 3.9+ machine.

## Development

```console
$ python -m pip install -e ".[dev]"
$ python -m pytest -q
........................................................................ [100%]
72 passed
```

The test suite is split by responsibility:

| File | Covers |
| --- | --- |
| `tests/test_query.py` | Tokenizer, path steps, evaluator, error types. |
| `tests/test_output.py` | `pretty`/`compact`/`jsonl`/`table` rendering, wide-character alignment. |
| `tests/test_cli.py` | End-to-end CLI: formats, `--raw`, stdin, exit codes, `--help`, `--version`. |

Layout:

```
src/jsonpeek/
    __init__.py     version
    __main__.py     python -m jsonpeek
    cli.py          argument parsing, IO, exit codes
    query.py        tokenizer + evaluator
    output.py       renderers
tests/              pytest suite and fixtures
examples/           sample JSON used by the README
```

## Contributing

Bug reports and pull requests are welcome. Please run `python -m pytest -q`
before opening a PR, keep the package standard-library-only, and add a test for
any behavior change.

## License

MIT — see [LICENSE](LICENSE).
