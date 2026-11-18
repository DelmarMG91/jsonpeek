#!/usr/bin/env bash
# Runnable walkthrough of jsonpeek. Run from the repository root:
#   bash examples/demo.sh
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-}:src"
PYTHON="${PYTHON:-python3}"

peek() { echo "\$ jsonpeek $*"; "$PYTHON" -m jsonpeek "$@"; echo; }

peek 'users[0].name' examples/users.json
peek 'users[*].name' examples/users.json
peek 'users[*].name' examples/users.json --format jsonl
peek 'users' examples/users.json --format table
peek 'items[*].sku' examples/inventory.json --format jsonl
peek 'items[1].qty' examples/inventory.json
peek '."a.b".c' examples/users.json

echo '$ echo '"'"'{"a":{"b":42}}'"'"' | jsonpeek '"'"'a.b'"'"' --raw'
echo '{"a":{"b":42}}' | "$PYTHON" -m jsonpeek 'a.b' --raw
