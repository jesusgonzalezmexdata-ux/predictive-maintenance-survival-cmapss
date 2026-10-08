# Source Qualification Report — 2026-10-07

Status: NON-NORMATIVE  
Companion JSON: `2026-10-07_SOURCE_INVENTORY.json`  
Invariant: `SOURCE != REQUIREMENT != DECISION != CANONICAL`

## Summary

Owner-placed materials exist under `intake/sources/`, but no canonical intent Markdown exists in `intake/` (templates/examples only). `discover-intents` returns `[]`. Sources support predictive-maintenance themes and conflict on primary modeling paradigm.

## Inventory (hashes)

| ID | Path | SHA256 (prefix) | Type | Trust |
|----|------|-----------------|------|-------|
| SRC-001 | `proyecto_5_datasets.txt` | `d0344079…` | URL notes | owner-placed |
| SRC-002 | `Proyecto_5_2020+…dataset.zip` | `f601f142…` | AI4I CSV zip | owner-placed |
| SRC-003 | `Proyect_5_Nasa.zip` | `7109344d…` | C-MAPSS expanded | owner-placed |
| SRC-004 | `Proyecto_5_Turbofan+…zip` | `c9c5dec1…` | C-MAPSS nested | owner-placed |
| SRC-005 | `DESARROLLO_GITHUB_PROYECTO_5.txt` | `e3b0c442…` (empty) | empty note | empty |

## Supported themes

- Predictive maintenance (tabular AI4I + turbofan degradation).
- RUL / progressive degradation / right-censoring relevance on NASA data.
- Possible survival framing (repo name + dataset note; not owner-promoted).

## Conflicts / ambiguities

1. **CNF-001** — AI4I tabular failure/cost framing vs NASA RUL/survival framing.
2. **CNF-002** — Duplicate NASA packaging (SRC-003 vs SRC-004).
3. Kaggle survival-preprocessed dataset referenced but not present locally.
4. Empty development note provides no GitHub/plan signal.

## Agent actions taken

- Qualified sources; did not ingest or invent `intake/*.md` intent.
- Emitted non-normative proposal + owner decision gate under `docs/proposals/`.

## Next authority

OWNER — decide `HG-001-SELECT-CANONICAL-OBJECTIVE`.
