from __future__ import annotations
from pathlib import Path
import json
from .utils import utcnow, sha256_bytes

GENESIS = 'GENESIS'

def _hash(entry):
    body = json.dumps(entry, sort_keys=True, separators=(',',':'), ensure_ascii=False).encode()
    return sha256_bytes(body)

def last_hash(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return GENESIS
    lines = [x for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
    return json.loads(lines[-1]).get('entry_hash', GENESIS) if lines else GENESIS

def append(root: Path, event: str, actor='repoctl', status='OBSERVED', details=None):
    path = root/'.logs/audit.jsonl'
    entry = {'timestamp':utcnow(),'event':event,'actor':actor,'status':status,'details':details or {},'prev_hash':last_hash(path)}
    entry['entry_hash'] = _hash(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(entry,ensure_ascii=False,sort_keys=True)+'\n')
    return entry

def verify(root: Path):
    path = root/'.logs/audit.jsonl'
    prev = GENESIS
    if not path.exists(): return False, 'audit log missing'
    for i,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: e=json.loads(line)
        except json.JSONDecodeError as exc: return False, f'line {i}: invalid JSON: {exc}'
        supplied=e.pop('entry_hash',None)
        if e.get('prev_hash') != prev: return False, f'line {i}: prev_hash mismatch'
        expected=_hash(e)
        if supplied != expected: return False, f'line {i}: entry_hash mismatch'
        prev=supplied
    return True, f'audit chain valid; head={prev}'
