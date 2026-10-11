#!/bin/sh
set -eu
bioforma_script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$bioforma_script_dir"
python3 -m venv .buildenv
.buildenv/bin/python -m pip install -r requirements-build.txt
exec .buildenv/bin/python build_executable.py
