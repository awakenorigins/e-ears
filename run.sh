#!/bin/bash
# E-Ears wrapper - activates venv and runs ears.py
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
python "$SCRIPT_DIR/scripts/ears.py" "$@"
