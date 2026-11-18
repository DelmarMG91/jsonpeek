# jsonpeek — Command-Line Reference

`jsonpeek` reads JSON from a file or standard input, evaluates a small path
expression against it, and prints the result. This page is the complete CLI
reference; for the expression grammar see [QUERY.md](QUERY.md), and for
task-oriented recipes see [EXAMPLES.md](EXAMPLES.md).

## Synopsis

```
jsonpeek EXPR [FILE] [--raw] [--format {pretty,compact,jsonl,table}]
               [--indent N] [--version] [--help]
```

## Arguments

| Argument | Description |
| --- | --- |
| `EXPR` | Path expression to evaluate, e.g. `users[0].name` or `users[*].id`. |
| `FILE` | JSON file to read. Omit, or pass `-`, to read standard input. |

## Options

| Option | Default | Description |
| --- | --- | --- |
| `--raw` | off | Print a selected **string** without JSON quotes or escapes. Useful inside shell pipelines. |
| `--format FORMAT` | `pretty` | One of `pretty`, `compact`, `jsonl`, `table`. |
| `--indent N` | `2` | Indentation width for the `pretty` format. `0` produces compact output. |
| `--version` | — | Print `jsonpeek <version>` and exit `0`. |
| `--help` | — | Show the built-in help and exit `0`. |

### Output formats

- **pretty** — `json.dumps(..., indent=N)`, the human default.
- **compact** — one line, no spaces (`json.dumps(..., separators=(",", ":"))`).
- **jsonl** — one JSON value per line; ideal for arrays of records and for
  `while read` loops.
- **table** — renders an array of objects as an aligned text table. Wide (CJK)
  characters are counted as two columns so mixed-language tables stay aligned.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success. |
| `2` | Invalid expression, malformed JSON, unreadable file, missing key, or out-of-range index. The message goes to stderr. |

## Examples

```console
$ jsonpeek 'users[0].name' examples/users.json
"Alice"

$ jsonpeek 'users[*].name' examples/users.json
[
  "Alice",
  "Bob",
  "Chen Wei"
]

$ jsonpeek 'users[*].name' examples/users.json --format jsonl
"Alice"
"Bob"
"Chen Wei"

$ echo '{"a":{"b":42}}' | jsonpeek 'a.b' --raw
42

$ jsonpeek 'users' examples/users.json --format table
id  name      role    active
--  --------  ------  ------
1   Alice     admin   true
2   Bob       editor  false
3   Chen Wei  viewer  true
```

## Piping and scripting

`--raw` plus `jsonl` make `jsonpeek` a good citizen in shell pipelines:

```console
# collect every active user's email into a file
$ jsonpeek 'users[*]' data.json --format jsonl \
    | while read -r row; do echo "$row" | jsonpeek 'email' --raw; done

# feed one value into another command
$ TOKEN=$(jsonpeek 'auth.token' config.json --raw)
```
