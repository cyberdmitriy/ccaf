#!/bin/bash
# UserPromptSubmit hook — deterministically rebuild+open the CCAF app when /ccaf:init or
# /ccaf:dashboard is typed. Fires on EVERY prompt, so filter fast and early-exit.
#
# Non-blocking by design: any failure exits 0 so the prompt still submits and the skill runs its
# fallback build. We never exit 2 (which would block the prompt). build-app.py guards the GUI on TTY.
set -uo pipefail
INPUT="$(cat)"
# Extract the prompt field without requiring jq (python3 is already a plugin dependency).
PROMPT="$(printf '%s' "$INPUT" | python3 -c 'import sys,json; print((json.load(sys.stdin).get("prompt") or "").strip())' 2>/dev/null || true)"
case "$PROMPT" in
  /ccaf:init*|/ccaf:dashboard*) ;;   # ours — rebuild below
  *) exit 0 ;;                        # anything else — pass through, negligible overhead
esac
python3 "${CLAUDE_PLUGIN_ROOT}/data/build-app.py" --open >/dev/null 2>&1 || exit 0
exit 0
