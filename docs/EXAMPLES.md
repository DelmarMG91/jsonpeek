# jsonpeek — Examples

Task-oriented recipes. All commands assume you are in the repository root and
that `jsonpeek` is installed (`pip install jsonpeek`) or run via
`python -m jsonpeek` with `PYTHONPATH=src`.

## 1. Pull a single field

```console
$ jsonpeek 'author.email' examples/users.json
"ada@example.com"
```

## 2. Collect one field across an array

```console
$ jsonpeek 'users[*].name' examples/users.json
[
  "Alice",
  "Bob",
  "Chen Wei"
]
```

## 3. Feed values into other tools (JSONL + while-read)

```console
$ jsonpeek 'users[*]' examples/users.json --format jsonl \
    | while read -r user; do
        printf '%s <%s>\n' \
          "$(echo "$user" | jsonpeek 'name' --raw)" \
          "$(echo "$user" | jsonpeek 'role' --raw)"
      done
Alice <admin>
Bob <editor>
Chen Wei <viewer>
```

## 4. Render records as a table

```console
$ jsonpeek 'users' examples/users.json --format table
id  name      role    active
--  --------  ------  ------
1   Alice     admin   true
2   Bob       editor  false
3   Chen Wei  viewer  true
```

## 5. Work with an inventory fixture

```console
$ jsonpeek 'items[*].sku' examples/inventory.json --format jsonl
"KB-01"
"MS-02"
"CB-03"

$ jsonpeek 'items[1].qty' examples/inventory.json
14
```

## 6. Dotted and quoted keys

```console
$ jsonpeek '."a.b".c' examples/users.json
"dotted"
```

## 7. Use it in a CI guard

```console
# fail the build if the manifest version drift from VERSION file
$ want=$(cat VERSION)
$ got=$(jsonpeek 'version' package.json --raw)
$ test "$want" = "$got" || { echo "version mismatch"; exit 1; }
```

Run the whole walkthrough non-interactively:

```console
$ bash examples/demo.sh
```
