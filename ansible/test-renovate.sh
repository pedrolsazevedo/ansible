#!/bin/bash
# Test Renovate with dry-run
# Usage: ./test-renovate.sh [validate|local|dry-run|run]

MODE=${1:-validate}

if [ "$MODE" = "validate" ]; then
  echo "Validating renovate.json..."
  docker run --rm \
    -v "$(pwd):/usr/src/app" \
    renovate/renovate:latest \
    renovate-config-validator
elif [ "$MODE" = "local" ]; then
  echo "Running against local files (no remote, no PRs)..."
  docker run --rm \
    -v "$(pwd):/usr/src/app" \
    -e LOG_LEVEL=info \
    -e RENOVATE_TOKEN=dummy \
    renovate/renovate:latest \
    --platform=local \
    --dry-run=full
elif [ "$MODE" = "dry-run" ] || [ "$MODE" = "run" ]; then
  if [ "$MODE" = "dry-run" ]; then
    echo "Running dry-run against GitHub..."
    DRY_RUN_FLAG="--dry-run=full"
  else
    echo "Running LIVE against GitHub (will create PRs)..."
    DRY_RUN_FLAG=""
  fi

  echo "Note: Requires GITHUB_TOKEN env var"

  if [ -z "$GITHUB_TOKEN" ]; then
    echo "ERROR: GITHUB_TOKEN not set"
    echo "Export your GitHub token: export GITHUB_TOKEN='your-token'"
    exit 1
  fi

  docker run --rm \
    -v "$(pwd):/usr/src/app" \
    -e LOG_LEVEL=info \
    -e RENOVATE_TOKEN="$GITHUB_TOKEN" \
    renovate/renovate:latest \
    --platform=github \
    $DRY_RUN_FLAG \
    pedrolsazevedo/ansible
else
  echo "Usage: $0 [validate|local|dry-run|run]"
  echo "  validate - Validate renovate.json only"
  echo "  local    - Run against local files without remote (no PRs)"
  echo "  dry-run  - Test against GitHub without creating PRs"
  echo "  run      - Run LIVE and create actual PRs"
  exit 1
fi
