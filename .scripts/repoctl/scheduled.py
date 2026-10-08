from __future__ import annotations
from pathlib import Path
import json, subprocess, sys
from .utils import utcnow, write_json
from .verify import run as verify_run
from .security import scan

def execute(root: Path, job: str):
    report={'job':job,'timestamp':utcnow(),'effect_scope':'EVIDENCE_ONLY','status':'PASS','findings':[]}
    if job=='daily-drift':
        for name,ok,detail in verify_run(root,fast=True):
            if not ok: report['findings'].append({'check':name,'detail':detail})
    elif job=='weekly-agent-qa':
        for name,ok,detail in verify_run(root,fast=False):
            if not ok: report['findings'].append({'check':name,'detail':detail})
        hits=scan(root)
        if hits: report['findings'].append({'check':'security-scan','detail':hits})
    elif job=='monthly-governance-review':
        report['effect_scope']='EVIDENCE_AND_PROPOSALS_ONLY'
        for name,ok,detail in verify_run(root,fast=False):
            if not ok: report['findings'].append({'check':name,'detail':detail})
        report['proposal']='Review incidents, adapter drift, benchmark failures and budget trends. No governance change is auto-promoted.'
    else:
        raise ValueError(f'Unknown scheduled job: {job}')
    if report['findings']: report['status']='ATTENTION_REQUIRED'
    safe=job.replace('/','-')
    path=root/'.logs/reports'/f'{utcnow().replace(":","-")}-{safe}.json'
    write_json(path,report)
    return path,report
