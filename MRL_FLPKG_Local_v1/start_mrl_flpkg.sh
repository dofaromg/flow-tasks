#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 -X utf8 "$base/mrl_local.py" serve "$@"
