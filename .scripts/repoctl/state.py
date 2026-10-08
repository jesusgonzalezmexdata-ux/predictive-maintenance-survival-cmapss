from __future__ import annotations
from pathlib import Path
from .utils import read_json

GOVERNANCE_ROOTS={'.agents','.federated','.hooks','.logs','.mda','.sandbox','.scripts','config','docs','test','intake','.cursor','.github','.gemini','.windsurf','.claude'}
GOVERNANCE_FILES={'README.md','AGENTS.md','CLAUDE.md','GEMINI.md','CONVENTIONS.md','Makefile','.gitignore','.gitattributes','.aider.conf.yml','VERSION','SECURITY.md','CHANGELOG.md','BASELINE_MANIFEST.sha256','pyproject.toml','.env.example'}
DECLARATIVE_SCOPE_FILES={'AGENTS.md','SCOPE_STATE.json','.gitkeep','OBJECTIVE.md','INTENT.md','VISION.md'}

def _registered_intents(root: Path):
    try:
        data=read_json(root/'config/intake-registry.json')
        return set(data.get('entries',{}))
    except Exception:
        return set()

def _has_product_content(path: Path, root: Path, registered):
    for p in path.rglob('*'):
        if not p.is_file(): continue
        if p.name in DECLARATIVE_SCOPE_FILES: continue
        try: rp=p.resolve().relative_to(root.resolve()).as_posix()
        except ValueError: rp=''
        if rp in registered: continue
        return True
    return False

def detect(root: Path):
    substantive=[]
    registered=_registered_intents(root)
    for p in root.iterdir():
        if p.name=='.git': continue
        if p.is_dir() and p.name in GOVERNANCE_ROOTS: continue
        if p.is_file() and p.name in GOVERNANCE_FILES: continue
        if p.is_dir() and not _has_product_content(p,root,registered): continue
        substantive.append(p.name)
    project=read_json(root/'config/project.json')
    return {
      'project_state':'BROWNFIELD' if substantive else 'GREENFIELD',
      'substantive_entries':sorted(substantive),
      'maturity':project['maturity'],
      'implementation_authority':project.get('implementation_authority','NONE_BY_DEFAULT'),
      'objective':project.get('objective','')
    }
