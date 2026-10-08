#!/usr/bin/env sh
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "Install these entries manually after review:"
echo "17 3 * * * cd $ROOT && python .scripts/repoctl.py scheduled daily-drift"
echo "31 4 * * 0 cd $ROOT && python .scripts/repoctl.py scheduled weekly-agent-qa"
echo "47 5 1 * * cd $ROOT && python .scripts/repoctl.py scheduled monthly-governance-review"
