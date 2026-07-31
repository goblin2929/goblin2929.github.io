#!/bin/bash
#
# Monthly bookkeeping runner for Novastacks AI.
# Invoked by launchd (com.novastacks.bookkeeping.monthly) on the 1st at ~07:00 local.
# Runs Claude Code headlessly against the monthly-bookkeeping-controller skill and
# emails the digest at the end.
#
# Config via environment (set by the launchd plist that install.sh generates):
#   BOOKKEEPING_EMAIL   (required) recipient for the digest email
#   CLAUDE_BIN          (optional) path/name of the Claude Code CLI, default: claude
#   BOOKKEEPING_WORKDIR (optional) working dir with MCP configured, default: $HOME
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
WORKDIR="${BOOKKEEPING_WORKDIR:-$HOME}"
EMAIL="${BOOKKEEPING_EMAIL:-}"
LOG_DIR="$HOME/Library/Logs/novastacks-bookkeeping"
PROMPT_TEMPLATE="$SCRIPT_DIR/bookkeeping-run-prompt.md"

mkdir -p "$LOG_DIR"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
LOG="$LOG_DIR/run_$STAMP.log"

echo "=== Novastacks monthly bookkeeping run $STAMP ===" | tee -a "$LOG"

if [ -z "$EMAIL" ]; then
  echo "ERROR: BOOKKEEPING_EMAIL is not set. Aborting." | tee -a "$LOG"
  exit 1
fi

if ! command -v "$CLAUDE_BIN" >/dev/null 2>&1; then
  echo "ERROR: Claude CLI '$CLAUDE_BIN' not found in PATH ($PATH)." | tee -a "$LOG"
  echo "Set CLAUDE_BIN to its absolute path (e.g. \$(which claude)) and reinstall." | tee -a "$LOG"
  exit 127
fi

if [ ! -f "$PROMPT_TEMPLATE" ]; then
  echo "ERROR: prompt template not found at $PROMPT_TEMPLATE." | tee -a "$LOG"
  exit 1
fi

# Inject the recipient at run time so the committed template stays address-free.
PROMPT="$(sed "s|__BOOKKEEPING_EMAIL__|${EMAIL}|g" "$PROMPT_TEMPLATE")"

cd "$WORKDIR"

# Headless, unattended. --dangerously-skip-permissions lets the MCP tool calls
# (Gmail / Airtable / Google Drive) run without an interactive approval prompt.
# See README for the tighter --allowedTools alternative.
"$CLAUDE_BIN" -p "$PROMPT" --dangerously-skip-permissions 2>&1 | tee -a "$LOG"

echo "=== Run finished: $STAMP ===" | tee -a "$LOG"
