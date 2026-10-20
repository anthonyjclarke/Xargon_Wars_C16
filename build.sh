#!/bin/sh
set -eu
cd "$(dirname "$0")"
exec "${PYTHON:-python3}" scripts/restore_c16.py "$@"
