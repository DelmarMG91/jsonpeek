# jsonpeek — Query Language

`jsonpeek` deliberately implements a *path* language, not a filter DSL. If you
can point at a value with dots and brackets, you can get it.

## Grammar

```
expression := root? segment+
root       := "$" | "@"          # optional, ignored
segment    := "." key
            | "." quoted_key
            | "[" index "]"
            | "[" "*" "]"
key        := /[^.\[\]]+/
quoted_key := '"' /[^"]+/ '"'
index      := integer            # negative counts from the end
```

## Segments

| Segment | Meaning | Example | Result on `{"a":{"b":1}}` |
| --- | --- | --- | --- |
| `.key` | Object member lookup. | `a.b` | `1` |
| `[i]` | Array element at index `i`. Negative indices count from the end. | `a[0]`, `a[-1]` | element value |
| `[*]` | Wildcard over an array (list of elements) or an object (list of values). | `a[*]` | `[...]` |
| `."quoted"` | Member whose name contains dots, spaces, or brackets. | `."a.b".c` | `"dotted"` |

The leading `$` or `@` is accepted purely so JSONPath muscle memory still works;
it carries no meaning.

## Semantics

- **Object lookup** on a missing key is an error (exit code `2`), never a silent
  `null`. This is intentional: a typo should fail loudly.
- **Array index** out of range is an error. Negative indices resolve against the
  current length (`-1` is the last element).
- **Wildcard** always yields a list, even when the source is an object or a
  single-element array. An empty array/object yields `[]`.
- **Scalar traversal** — applying a key or index to a scalar is an error.

## Examples

```console
$ echo '{"a":{"b":1}}'        | jsonpeek 'a.b'
1
$ echo '{"a":[10,20,30]}'     | jsonpeek 'a[-1]'
30
$ echo '{"a":{"x":1,"y":2}}'  | jsonpeek 'a[*]'
[
  1,
  2
]
$ echo '{"a.b":{"c":"dotted"}}' | jsonpeek '."a.b".c'
"dotted"
$ echo '{"users":[{"id":1}]}' | jsonpeek '$.users[*].id'
[
  1
]
```

## Error messages

Errors are printed to stderr with a stable prefix so they are easy to catch:

```console
$ echo '{"a":1}' | jsonpeek 'b'
jsonpeek: query failed: missing key 'b'
[exit 2]

$ echo 'not json' | jsonpeek 'a'
jsonpeek: error: invalid JSON in <stdin> at line 1 column 1: Expecting value
[exit 2]
```
