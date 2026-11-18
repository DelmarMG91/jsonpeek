# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No unreleased changes yet._

## [0.1.1] - 2026-11-18

### Added

- Animated terminal demo (`docs/demo.gif`) and a runnable `examples/demo.sh`.
- `docs/USAGE.md` (CLI reference), `docs/QUERY.md` (grammar) and
  `docs/EXAMPLES.md` (recipes).
- `examples/inventory.json` fixture.
- A PyPI publish workflow (`.github/workflows/publish.yml`) using Trusted
  Publishing, plus a `pip install jsonpeek` section in the README.

## [0.1.0] - 2025-11-18

### Added

- Path expression tokenizer and evaluator supporting nested keys (`a.b.c`),
  array indices (`users[0].name`, negative indices included), wildcard
  projection (`users[*].name`), quoted keys (`."a.b".c`) and the optional `$`/`@`
  root prefix.
- `jsonpeek` CLI with `EXPR [FILE]`, stdin support when `FILE` is omitted or `-`,
  `--raw`, `--format pretty|compact|jsonl|table`, `--indent N` and `--version`.
- Output renderers for pretty, compact, JSON Lines and aligned tables, including
  East-Asian wide-character aware column widths.
- Distinct error types (`QuerySyntaxError`, `QueryKeyError`, `QueryIndexError`,
  `QueryTypeError`) surfaced on stderr with exit code `2`.
- pytest suite covering the tokenizer, evaluator, renderers and the CLI end to
  end, with a fixture-driven stdin/file matrix.

[Unreleased]: https://github.com/DelmarMG91/jsonpeek/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/DelmarMG91/jsonpeek/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/DelmarMG91/jsonpeek/releases/tag/v0.1.0
