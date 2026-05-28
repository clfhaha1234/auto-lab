#!/usr/bin/env bash
# Asserts SKILL.md (root, for ~/.claude/skills/auto-itera git-clone install)
# and skills/auto-itera/SKILL.md (for Claude Code plugin marketplace install)
# are byte-identical. If they drift, the plugin install ships stale content.
#
# Sync from root after editing SKILL.md:
#   cp SKILL.md skills/auto-itera/SKILL.md
set -euo pipefail
ROOT_HASH=$(shasum -a 256 SKILL.md | awk '{print $1}')
PLUG_HASH=$(shasum -a 256 skills/auto-itera/SKILL.md | awk '{print $1}')
if [ "$ROOT_HASH" != "$PLUG_HASH" ]; then
  echo "ERROR: SKILL.md and skills/auto-itera/SKILL.md have drifted." >&2
  echo "  root: $ROOT_HASH" >&2
  echo "  plug: $PLUG_HASH" >&2
  echo "Fix: cp SKILL.md skills/auto-itera/SKILL.md" >&2
  exit 1
fi
echo "ok: SKILL.md and skills/auto-itera/SKILL.md are in sync ($ROOT_HASH)"
