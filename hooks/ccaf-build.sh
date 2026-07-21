#!/bin/bash
# UserPromptSubmit hook — deterministically rebuild+open the CCAF app when /ccaf:init or
# /ccaf:dashboard is typed. Fires on EVERY prompt, so filter fast and early-exit.
#
# Non-blocking by design: any failure exits 0 so the prompt still submits and the skill runs its
# fallback build. We never exit 2 (which would block the prompt). build-app.py guards the GUI on TTY.
set -uo pipefail
INPUT="$(cat)"
# Cheap bash prefilter: if the raw stdin can't possibly contain our command, skip python entirely
# (saves a ~30–80ms python cold-start on the ~99% of prompts that aren't /ccaf:*).
case "$INPUT" in *ccaf*) ;; *) exit 0 ;; esac
# Extract the prompt field without requiring jq (python3 is already a plugin dependency).
PROMPT="$(printf '%s' "$INPUT" | python3 -c 'import sys,json; print((json.load(sys.stdin).get("prompt") or "").strip())' 2>/dev/null || true)"
case "$PROMPT" in
  /ccaf:init*|/ccaf:dashboard*) ;;   # ours — rebuild below
  *) exit 0 ;;                        # anything else — pass through, negligible overhead
esac
# CLAUDE_PLUGIN_ROOT should always be set for a plugin hook; if not, no-op quietly (never block).
[ -n "${CLAUDE_PLUGIN_ROOT:-}" ] || exit 0
# Rebuild + open (build-app.py opens unless CCAF_NO_OPEN is set). On success, print a marker to
# stdout — UserPromptSubmit stdout is injected into the model's context, so the skill/command can
# SEE the hook already rebuilt & opened the app and skip its own build (avoids a double build).
if python3 "${CLAUDE_PLUGIN_ROOT}/data/build-app.py" --open >/dev/null 2>&1; then
  echo "[ccaf-hook] Rebuilt & opened ~/.claude/ccaf-progress/ccaf-exam.html — the app is already fresh and open. Do NOT run the build again; just report/route."
fi
exit 0
