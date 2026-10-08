from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os

def utcnow():
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    tmp.replace(path)

def sha256_bytes(data: bytes):
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path):
    return sha256_bytes(path.read_bytes())

def repo_root(start: Path | None = None):
    p = (start or Path.cwd()).resolve()
    for candidate in [p, *p.parents]:
        if (candidate/'.mda/manifest.json').exists():
            return candidate
    raise RuntimeError('Not inside an MDA-governed repository (.mda/manifest.json missing).')

def rel(root: Path, path: Path):
    return path.resolve().relative_to(root.resolve()).as_posix()
