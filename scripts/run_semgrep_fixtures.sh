#!/usr/bin/env bash
set -euo pipefail

mkdir -p reports/semgrep

semgrep scan \
  --config p/default \
  --metrics off \
  --json-output reports/semgrep/fixtures-mvp-semgrep.json \
  fixtures/mvp

semgrep scan \
  --config p/default \
  --metrics off \
  fixtures/mvp
