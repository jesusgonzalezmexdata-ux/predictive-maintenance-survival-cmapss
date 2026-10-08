from __future__ import annotations
from pathlib import Path
import json
from .utils import read_json
from .adapters import drift
from .audit import verify as verify_audit

REQUIRED=['README.md','Makefile','.gitignore','.mda/manifest.json','.mda/source/behavior.mda.md','.mda/source/intake.mda.json','.mda/source/scaffold-profiles.mda.json','.mda/schemas/intent.schema.json','config/project.json','config/authority.json','config/intake.json','config/intake-registry.json','intake/OBJECTIVE_TEMPLATE.md','.scripts/repoctl.py']

def run(root: Path, fast=False):
    checks=[]
    missing=[x for x in REQUIRED if not (root/x).exists()]
    checks.append(('required-files',not missing,missing or 'ok'))
    parse_targets=['.mda/manifest.json','.mda/source/capability-map.mda.json','.mda/source/maturity.mda.json','.mda/source/authority.mda.json','.mda/source/events.mda.json','.mda/source/folders.mda.json','.mda/source/intake.mda.json','.mda/source/scaffold-profiles.mda.json','config/project.json','config/authority.json','config/intake.json','config/intake-registry.json','config/routing.json','config/budgets.json','config/schedules.json','config/security.json','config/tooling.json']
    errors=[]
    for rel in parse_targets:
        try: read_json(root/rel)
        except Exception as e: errors.append(f'{rel}: {e}')
    checks.append(('json-parse',not errors,errors or 'ok'))
    try:
        caps=read_json(root/'.mda/source/capability-map.mda.json')['capabilities']
        pts=sorted(c['point'] for c in caps)
        valid=pts==list(range(1,20)) and len({c['id'] for c in caps})==19
        checks.append(('capabilities-1-19',valid,pts))
    except Exception as e: checks.append(('capabilities-1-19',False,str(e)))
    try:
        intake=read_json(root/'config/intake.json')
        ok=intake.get('auto_implement_product') is False and intake.get('default_materialization')=='SCAFFOLD_ONLY'
        checks.append(('intake-safety',ok,{'auto_implement_product':intake.get('auto_implement_product'),'default_materialization':intake.get('default_materialization')}))
    except Exception as e: checks.append(('intake-safety',False,str(e)))
    d=drift(root); checks.append(('adapter-drift',not d,d or 'ok'))
    if not fast:
        ok,msg=verify_audit(root); checks.append(('audit-chain',ok,msg))
    return checks
