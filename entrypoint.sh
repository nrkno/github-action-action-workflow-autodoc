#!/bin/bash
echo "Current directoryy: $(pwd)"

python3 /autodoc.py

git config user.name "GitHub Actions Bot"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add "${INPUT_DOC_FILE}" && git commit -m "${INPUT_COMMIT_MESSAGE}" && git push
