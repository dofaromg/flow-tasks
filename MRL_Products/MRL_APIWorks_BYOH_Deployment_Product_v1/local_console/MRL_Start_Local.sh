#!/bin/sh
set -eu
MRL_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "${MRL_PYTHON:-python3}" "$MRL_SCRIPT_DIR/MRL_local_console_v1.py" "$@"
