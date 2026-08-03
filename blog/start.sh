#!/bin/bash
# One-command way to start the blog publish tool.
# Usage:  bash /Users/isakzvegelj/projects/personal-site/blog/start.sh
cd "$(dirname "$0")"
echo "Opening blog publish tool in your browser…"
python3 publish.py
