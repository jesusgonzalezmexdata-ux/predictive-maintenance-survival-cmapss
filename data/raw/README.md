# data/raw — Raw data boundary (SPEC-001 §4.1)

Governed scope. Write policy: `APPROVED_TASK` (TASK-001).

## What lives here

- `MANIFEST.json` — provenance of the canonical archive (DEC-003 = SRC-003
  `intake/sources/Proyect_5_Nasa.zip`, SHA256 `7109344d…`), per-file hashes,
  sizes and row counts, and the column contract (26 columns).
- `cmapss/` — **local extraction only, gitignored (DEC-004)**. Regenerate with:

```bash
.venv/Scripts/python -m pm_survival extract --archive intake/sources/Proyect_5_Nasa.zip --out data/raw/cmapss
```

(The `extract` subcommand is delivered in TASK-006; until then TASK-001 performed the
extraction once and recorded hashes in the manifest.)

## Rules

- Nothing here is modified in place; raw files are immutable inputs.
- No dataset is committed to git; no network download happens at runtime.
- Ground-truth `RUL_FD00x.txt` is evaluation-only and must never be joined as a feature.

## Schema (per row)

`unit_id, cycle, op_setting_1..3, sensor_1..21` — whitespace separated, trailing spaces allowed.

| Subset | Train rows | Train units | Test rows | Test units |
|--------|-----------:|------------:|----------:|-----------:|
| FD001 | 20 631 | 100 | 13 096 | 100 |
| FD002 | 53 759 | 260 | 33 991 | 259 |
| FD003 | 24 720 | 100 | 16 596 | 100 |
| FD004 | 61 249 | 249 | 41 214 | 248 |

Only FD001 is in scope for SPEC-001.
