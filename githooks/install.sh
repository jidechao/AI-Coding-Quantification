#!/usr/bin/env bash
set -euo pipefail

TARGET_REPO="${1:-$(pwd)}"
HOOK_DIR="${TARGET_REPO}/.git/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -d "${TARGET_REPO}/.git" ]]; then
  echo "[ai-metrics] target is not a git repository: ${TARGET_REPO}" >&2
  exit 1
fi

mkdir -p "${HOOK_DIR}/ai-metrics-lib"
cp "${SCRIPT_DIR}/prepare-commit-msg" "${HOOK_DIR}/prepare-commit-msg"
cp "${SCRIPT_DIR}/commit-msg" "${HOOK_DIR}/commit-msg"
cp "${SCRIPT_DIR}/post-commit" "${HOOK_DIR}/post-commit"
cp -R "${SCRIPT_DIR}/lib/." "${HOOK_DIR}/ai-metrics-lib/"
chmod +x "${HOOK_DIR}/prepare-commit-msg" "${HOOK_DIR}/commit-msg" "${HOOK_DIR}/post-commit"

echo "[ai-metrics] hooks installed into ${HOOK_DIR}"
