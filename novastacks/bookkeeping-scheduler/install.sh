#!/bin/bash
#
# One-time installer for the monthly bookkeeping scheduled job on the Mac mini.
# Generates a launchd LaunchAgent that fires on the 1st of each month at 07:00 local,
# then loads it. Re-run any time to update the schedule or the recipient.
#
# Usage:
#   BOOKKEEPING_EMAIL=you@example.com ./install.sh
# Optional overrides:
#   CLAUDE_BIN=/opt/homebrew/bin/claude BOOKKEEPING_EMAIL=you@example.com ./install.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNNER="$SCRIPT_DIR/run-monthly-bookkeeping.sh"
LABEL="com.novastacks.bookkeeping.monthly"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$HOME/Library/Logs/novastacks-bookkeeping"

EMAIL="${BOOKKEEPING_EMAIL:-}"
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || true)}"
# Include common Homebrew locations so launchd (which has a minimal PATH) finds claude.
RUN_PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

if [ -z "$EMAIL" ]; then
  echo "ERROR: set BOOKKEEPING_EMAIL, e.g.  BOOKKEEPING_EMAIL=you@example.com ./install.sh"
  exit 1
fi
if [ -z "$CLAUDE_BIN" ]; then
  echo "ERROR: could not find the 'claude' CLI. Install Claude Code, or pass CLAUDE_BIN=/path/to/claude."
  exit 1
fi

chmod +x "$RUNNER"
mkdir -p "$LOG_DIR" "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$RUNNER</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>BOOKKEEPING_EMAIL</key><string>$EMAIL</string>
        <key>CLAUDE_BIN</key><string>$CLAUDE_BIN</string>
        <key>PATH</key><string>$RUN_PATH</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Day</key><integer>1</integer>
        <key>Hour</key><integer>7</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
    <key>StandardOutPath</key><string>$LOG_DIR/launchd.out.log</string>
    <key>StandardErrorPath</key><string>$LOG_DIR/launchd.err.log</string>
    <key>RunAtLoad</key><false/>
</dict>
</plist>
PLIST

# (Re)load the agent.
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Installed: $LABEL"
echo "  Runner : $RUNNER"
echo "  Email  : $EMAIL"
echo "  Claude : $CLAUDE_BIN"
echo "  Plist  : $PLIST"
echo "  Logs   : $LOG_DIR/"
echo ""
echo "Next scheduled run: 1st of each month at 07:00 local."
echo "Dry-run it now with:   launchctl start $LABEL"
echo "Then watch the log:    tail -f \"$LOG_DIR\"/run_*.log"
echo "Uninstall with:        launchctl unload \"$PLIST\" && rm \"$PLIST\""
