#!/usr/bin/env bash
set -euo pipefail

mkdir -p reports/bandit
bandit -c pyproject.toml -r fixtures/mvp -f json -o reports/bandit/fixtures-mvp-bandit.json
bandit -c pyproject.toml -r fixtures/mvp
