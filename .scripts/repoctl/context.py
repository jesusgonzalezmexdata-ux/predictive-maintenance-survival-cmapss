from __future__ import annotations
from pathlib import Path
from .utils import rel

def effective_files(root: Path, target: Path):
    t=(root/target).resolve() if not target.is_absolute() else target.resolve()
    if t.is_file(): t=t.parent
    files=[]
    root_agents=root/'AGENTS.md'
    if root_agents.exists(): files.append(root_agents)
    try: rp=t.relative_to(root)
    except ValueError: raise RuntimeError('Target is outside repository.')
    cur=root
    for part in rp.parts:
        cur=cur/part
        p=cur/'AGENTS.md'
        if p.exists() and p != root_agents: files.append(p)
    return files

def package(root: Path, target: Path):
    fs=effective_files(root,target)
    return {'target':target.as_posix(),'instruction_files':[rel(root,p) for p in fs],'content':'\n\n'.join(p.read_text(encoding='utf-8') for p in fs)}
