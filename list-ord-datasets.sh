#!/bin/sh
# Lists all ORD dataset names from https://github.com/open-reaction-database/ord-data/tree/main/data
# Each dataset is a file (e.g. ord_dataset-<hash>.pb.gz) nested in per-prefix subdirectories.
# We use only the file name without extension (the part before the first dot).
#
# The names are appended to the target file, but only those not already present,
# so existing entries and their order are preserved.
#
# Usage: ./list-ord-datasets.sh [target-file]   (default: src/elsci_ordtomeve/datasets.txt)

set -e

REPO="open-reaction-database/ord-data"
BRANCH="main"
TARGET="${1:-src/elsci_ordtomeve/datasets.txt}"

touch "$TARGET"

# Fetch the full recursive tree in one request. Keep only files (blobs) under
# data/, take the file name (basename) and drop everything from the first dot.
names=$(curl -sSL "https://api.github.com/repos/${REPO}/git/trees/${BRANCH}?recursive=1" \
  | jq -r '.tree[] | select(.type == "blob" and (.path | startswith("data/"))) | .path' \
  | sed -E 's#.*/##; s#\..*##' \
  | grep -v '^$' \
  | sort -u)

# Append only the names that aren't already in the target file (fixed-string,
# whole-line match). Ensure the target ends with a newline before appending.
printf '%s\n' "$names" | while IFS= read -r name; do
  if ! grep -qxF "$name" "$TARGET"; then
    [ -s "$TARGET" ] && [ -n "$(tail -c1 "$TARGET")" ] && echo "" >> "$TARGET"
    echo "$name" >> "$TARGET"
    echo "added: $name" >&2
  fi
done
