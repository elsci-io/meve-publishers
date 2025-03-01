#!/bin/sh
. .venv/bin/activate
PYTHONPATH=./src uv run -- python src/elsci_ordtomeve/ord_to_meve.py