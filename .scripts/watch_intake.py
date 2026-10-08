#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, time
from pathlib import Path
from repoctl.utils import repo_root
from repoctl.intent import reconcile
from repoctl.audit import append as audit_append

def main():
    p=argparse.ArgumentParser(description='Event-style intake watcher for owner-controlled Markdown intent.')
    p.add_argument('--interval',type=float,default=3.0)
    p.add_argument('--once',action='store_true')
    args=p.parse_args(); root=repo_root()
    while True:
        results=reconcile(root,materialize=True)
        changed=[x for x in results if x['status'] not in {'UNCHANGED'}]
        if changed:
            audit_append(root,'intent_reconcile',actor='OWNER_INBOX',details={'results':changed})
            print(json.dumps(changed,indent=2,ensure_ascii=False),flush=True)
        if args.once: return 0
        time.sleep(max(args.interval,1.0))
if __name__=='__main__': raise SystemExit(main())
