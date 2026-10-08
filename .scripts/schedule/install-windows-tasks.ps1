$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
Write-Host "Review before running schtasks. Suggested commands:"
Write-Host "Daily:   cd $Root; python .scripts/repoctl.py scheduled daily-drift"
Write-Host "Weekly:  cd $Root; python .scripts/repoctl.py scheduled weekly-agent-qa"
Write-Host "Monthly: cd $Root; python .scripts/repoctl.py scheduled monthly-governance-review"
