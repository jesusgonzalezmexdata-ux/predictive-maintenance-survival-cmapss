PYTHON ?= python
REPOCTL := $(PYTHON) .scripts/repoctl.py

.PHONY: help inspect intents intake watch-intake compile preflight verify verify-fast test security audit agent-qa reconcile daily weekly monthly install-hooks
help:
	@echo "inspect intents intake watch-intake compile preflight verify test security audit reconcile daily weekly monthly install-hooks"
inspect:
	@$(REPOCTL) inspect
intents:
	@$(REPOCTL) discover-intents
intake:
	@$(REPOCTL) reconcile-intake
watch-intake:
	@$(PYTHON) .scripts/watch_intake.py
compile:
	@$(REPOCTL) compile
preflight:
	@$(REPOCTL) preflight --path .
verify:
	@$(REPOCTL) verify
verify-fast:
	@$(REPOCTL) verify --fast
test:
	@$(PYTHON) -m unittest discover -s test -p 'test_*.py'
security:
	@$(REPOCTL) security-scan
audit:
	@$(REPOCTL) audit-verify
agent-qa: test verify security
reconcile: intake compile verify

daily:
	@$(REPOCTL) scheduled daily-drift
weekly:
	@$(REPOCTL) scheduled weekly-agent-qa
monthly:
	@$(REPOCTL) scheduled monthly-governance-review
install-hooks:
	@$(REPOCTL) install-hooks
