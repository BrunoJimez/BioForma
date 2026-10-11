#!/bin/sh
set -eu
bioforma_script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$bioforma_script_dir"
exec python3 -m unittest discover -s tests -v
