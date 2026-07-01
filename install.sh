#!/usr/bin/env bash
# install.sh — install shopify-theme-builder as a Claude Code / Claude apps skill.
# For other agents (Codex, Cursor, Windsurf) you don't need this: just keep the
# repo in your project — they read AGENTS.md / .cursor/ / .windsurf/ directly.
#
# Usage:
#   ./install.sh            # install to ~/.claude/skills (all projects)
#   ./install.sh --project  # install to ./.claude/skills (current project)
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="shopify-theme-builder"

if [[ "${1:-}" == "--project" ]]; then
  DEST_ROOT=".claude/skills"
else
  DEST_ROOT="${HOME}/.claude/skills"
fi

DEST="${DEST_ROOT}/${SKILL_NAME}"
mkdir -p "${DEST_ROOT}"
rm -rf "${DEST}"
# Copy the skill payload (skip agent-adapter + VCS files not needed by Claude).
cp -R "${SRC_DIR}/" "${DEST}/"
rm -rf "${DEST}/.git" "${DEST}/.cursor" "${DEST}/.windsurf" "${DEST}/node_modules"

echo "Installed '${SKILL_NAME}' -> ${DEST}"
echo "Restart Claude Code (or start a new session), then ask: \"build a Shopify theme\"."
