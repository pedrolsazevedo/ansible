#!/bin/bash
# Shim - delegates to deploy.py
exec "$(dirname "$0")/main.py" "$@"
