#!/bin/bash
# One-command way to start the blog publish tool.
# Usage from the repository root:  bash blog/start.sh
cd "$(dirname "$0")"
echo "Opening blog publish tool in your browser…"
python3 publish.py
