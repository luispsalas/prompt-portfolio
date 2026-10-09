#!/bin/sh
# Create the local environment for the prompt-portfolio harness.
# Installs only into ./.venv; nothing outside this folder is touched.
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
echo "ready: $(.venv/bin/python -c 'import anthropic; print("anthropic", anthropic.__version__)')"
