# Onboarding

1. Install Python 3.11+ and Git. `make` is optional.
2. Run `python .scripts/repoctl.py inspect`.
3. Run `python .scripts/repoctl.py compile --check`.
4. Run `python .scripts/repoctl.py verify` and unit tests.
5. Initialize Git if this is a fresh copy, then run `python .scripts/repoctl.py install-hooks`.
6. Declare the project objective in `config/project.json` before product implementation.
7. Create governed specs/tasks under `docs/specs` and `docs/tasks`.

## Intent-first onboarding (v2)

If the repository has not yet been architected, begin from a Markdown intent rather than from code. Put the file in `intake/` or use a recognized `OBJECTIVE.md`, `INTENT.md` or `VISION.md` in the future target folder, then run `repoctl reconcile-intake`. Review `docs/intents/<INTENT-ID>/` before starting implementation.
