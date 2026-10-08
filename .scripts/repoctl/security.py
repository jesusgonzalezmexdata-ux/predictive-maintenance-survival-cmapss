from __future__ import annotations
from pathlib import Path
import re
from .utils import read_json, rel

def scan(root: Path):
    cfg=read_json(root/'config/security.json')
    patterns=[re.compile(p) for p in cfg['secret_patterns']]
    ignored=tuple(cfg.get('ignored_paths',[]))
    hits=[]
    for p in root.rglob('*'):
        if not p.is_file(): continue
        rp=rel(root,p)
        if rp == 'config/security.json': continue
        if rp.startswith(ignored) or '/.git/' in '/'+rp: continue
        if p.stat().st_size > 2_000_000: continue
        try: text=p.read_text(encoding='utf-8')
        except UnicodeDecodeError: continue
        for pat in patterns:
            m=pat.search(text)
            if m:
                hits.append({'path':rp,'pattern':pat.pattern,'sample':m.group(0)[:32]})
                break
    return hits
