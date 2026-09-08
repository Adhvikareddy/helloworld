#!/usr/bin/env bash
set -e
export PYTHONPATH=.
python scripts/e2e_smoke_test.py "$@"
