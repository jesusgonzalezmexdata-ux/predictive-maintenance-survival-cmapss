from __future__ import annotations
from pathlib import Path
import argparse, json, shutil, sys, os
from .utils import repo_root, read_json, utcnow
from .state import detect
from .context import package
from .adapters import compile_all, drift
from .verify import run as verify_run
from .audit import append as audit_append, verify as audit_verify
from .security import scan as security_scan
from .scheduled import execute as scheduled_execute
from .intent import discover as intent_discover, ingest as intent_ingest, reconcile as intent_reconcile

def _print(data):
    print(json.dumps(data,indent=2,ensure_ascii=False) if not isinstance(data,str) else data)

def _status(root):
    tools=['git','python','claude','codex','gemini','cursor-agent','aider','ollama']
    return {x:bool(shutil.which(x)) for x in tools}

def parser():
    p=argparse.ArgumentParser(prog='repoctl',description='MDA-governed repository control plane')
    s=p.add_subparsers(dest='cmd',required=True)
    s.add_parser('inspect')
    sp=s.add_parser('compile'); sp.add_argument('--check',action='store_true')
    sp=s.add_parser('preflight'); sp.add_argument('--path',default='.')
    sp=s.add_parser('context'); sp.add_argument('path',nargs='?',default='.')
    sp=s.add_parser('verify'); sp.add_argument('--fast',action='store_true')
    s.add_parser('audit-verify')
    sp=s.add_parser('audit-append'); sp.add_argument('event'); sp.add_argument('--actor',default='repoctl'); sp.add_argument('--status',default='OBSERVED')
    s.add_parser('security-scan')
    sp=s.add_parser('scheduled'); sp.add_argument('job',choices=['daily-drift','weekly-agent-qa','monthly-governance-review'])
    s.add_parser('install-hooks')
    s.add_parser('capabilities')
    sp=s.add_parser('init-project'); sp.add_argument('--name',required=True); sp.add_argument('--objective',required=True); sp.add_argument('--kind',default='UNDECLARED'); sp.add_argument('--authority',required=True)
    sp=s.add_parser('declare-scope'); sp.add_argument('path'); sp.add_argument('--objective',required=True); sp.add_argument('--write-policy',default='APPROVED_TASK'); sp.add_argument('--authority',required=True)
    sp=s.add_parser('propose-scope'); sp.add_argument('path'); sp.add_argument('--objective',required=True)
    sp=s.add_parser('ingest'); sp.add_argument('path'); sp.add_argument('--proposal-only',action='store_true')
    s.add_parser('discover-intents')
    sp=s.add_parser('reconcile-intake'); sp.add_argument('--proposal-only',action='store_true')
    return p

def main(argv=None):
    args=parser().parse_args(argv); root=repo_root()
    if args.cmd=='inspect':
        sources=intent_discover(root)
        registry=read_json(root/'config/intake-registry.json').get('entries',{})
        pending=[x for x in sources if x not in registry]
        changed=[]
        import hashlib
        for x in sources:
            if x in registry and (root/x).exists():
                h=hashlib.sha256((root/x).read_bytes()).hexdigest()
                if h != registry[x].get('content_hash'): changed.append(x)
        _print({'repository':root.name,'state':detect(root),'intent_status':{'discovered':sources,'pending':pending,'changed':changed},'tool_detection':_status(root),'adapter_drift':drift(root)})
        return 0
    if args.cmd=='compile':
        if args.check:
            d=drift(root); _print({'status':'PASS' if not d else 'DRIFT','drift':d}); return 0 if not d else 2
        files=compile_all(root); audit_append(root,'adapters_compiled',details={'files':files}); _print({'status':'PASS','generated':files}); return 0
    if args.cmd=='preflight':
        target=Path(args.path); st=detect(root); ctx=package(root,target)
        sources=intent_discover(root); registry=read_json(root/'config/intake-registry.json').get('entries',{}); pending=[x for x in sources if x not in registry]
        result={'status':'PASS','effectful_work':'BLOCKED' if st['implementation_authority']=='NONE_BY_DEFAULT' else 'TASK_SCOPED','state':st,'intent_status':{'pending':pending},'context':{'target':ctx['target'],'instruction_files':ctx['instruction_files']},'rules':['No self-promotion','Use deterministic verification','Empty target is not permission to invent requirements','Pending owner intent must be normalized before inventing topology']}
        audit_append(root,'preflight',details={'target':args.path,'project_state':st['project_state']}); _print(result); return 0
    if args.cmd=='context': _print(package(root,Path(args.path))); return 0
    if args.cmd=='verify':
        checks=verify_run(root,args.fast); ok=all(x[1] for x in checks); _print({'status':'PASS' if ok else 'FAIL','checks':[{'name':n,'pass':o,'detail':d} for n,o,d in checks]}); return 0 if ok else 2
    if args.cmd=='audit-verify':
        ok,msg=audit_verify(root); _print({'status':'PASS' if ok else 'FAIL','detail':msg}); return 0 if ok else 2
    if args.cmd=='audit-append': _print(audit_append(root,args.event,args.actor,args.status)); return 0
    if args.cmd=='security-scan':
        hits=security_scan(root); _print({'status':'PASS' if not hits else 'FAIL','findings':hits}); return 0 if not hits else 2
    if args.cmd=='scheduled':
        path,report=scheduled_execute(root,args.job); audit_append(root,'scheduled_job',status=report['status'],details={'job':args.job,'report':path.relative_to(root).as_posix()}); _print(report); return 0 if report['status']=='PASS' else 2
    if args.cmd=='install-hooks':
        git=root/'.git'
        if not git.exists(): _print({'status':'BLOCKED','reason':'Initialize Git first: git init'}); return 2
        hooks=git/'hooks'; hooks.mkdir(parents=True,exist_ok=True)
        for name in ['pre-commit','pre-push']:
            src=root/'.hooks/git'/name; dst=hooks/name; dst.write_bytes(src.read_bytes()); dst.chmod(0o755)
        audit_append(root,'git_hooks_installed',details={'hooks':['pre-commit','pre-push']}); _print({'status':'PASS'}); return 0
    if args.cmd=='capabilities':
        caps=read_json(root/'.mda/source/capability-map.mda.json'); _print(caps); return 0
    if args.cmd=='init-project':
        if args.authority != 'OWNER': _print({'status':'BLOCKED','reason':'OWNER authority required'}); return 2
        from .utils import write_json
        cfg=read_json(root/'config/project.json'); cfg.update({'project_name':args.name,'objective':args.objective,'project_kind':args.kind,'repository_mode':'PROJECT','implementation_authority':'TASK_SCOPED'})
        write_json(root/'config/project.json',cfg); audit_append(root,'project_initialized',actor='OWNER',details={'name':args.name,'kind':args.kind}); _print({'status':'PASS','project':cfg}); return 0
    if args.cmd=='declare-scope':
        if args.authority != 'OWNER': _print({'status':'BLOCKED','reason':'OWNER authority required'}); return 2
        from .utils import write_json
        relpath=Path(args.path).as_posix().strip('/')
        if not relpath or relpath.startswith('..') or relpath.startswith('.'):
            _print({'status':'BLOCKED','reason':'Product scope must be a relative non-hidden path'}); return 2
        data=read_json(root/'.mda/source/folders.mda.json')
        if relpath in data['folders']:
            _print({'status':'BLOCKED','reason':'Scope already declared'}); return 2
        data['folders'][relpath]={'purpose':args.objective,'write_policy':args.write_policy,'forbid':['secrets','writes outside approved task scope'],'scope_class':'PRODUCT','state':'DECLARED_UNMATERIALIZED'}
        write_json(root/'.mda/source/folders.mda.json',data); files=compile_all(root); audit_append(root,'scope_declared',actor='OWNER',details={'scope':relpath,'objective':args.objective}); _print({'status':'PASS','scope':relpath,'state':'DECLARED_UNMATERIALIZED'}); return 0
    if args.cmd=='discover-intents':
        _print({'status':'PASS','sources':intent_discover(root)}); return 0
    if args.cmd=='ingest':
        try:
            result=intent_ingest(root,Path(args.path),materialize=not args.proposal_only)
        except Exception as e:
            _print({'status':'BLOCKED','reason':str(e)}); return 2
        audit_append(root,'intent_ingested',actor='OWNER_LOCAL',details={'source':result['contract']['source'],'intent_id':result['contract']['intent_id'],'state':result['contract']['state'],'scopes':result['scopes_created'],'conflicts':result['conflicts']})
        status='BLOCKED' if result['conflicts'] or result['contract']['missing_decisions'] else 'PASS'
        _print({'status':status,**result}); return 0 if status=='PASS' else 2
    if args.cmd=='reconcile-intake':
        results=intent_reconcile(root,materialize=not args.proposal_only)
        changed=[x for x in results if x.get('status')!='UNCHANGED']
        if changed: audit_append(root,'intent_reconcile',actor='OWNER_INBOX',details={'results':changed})
        bad=[x for x in results if x.get('status') in {'ERROR','CHANGED_REQUIRES_EXPLICIT_REINGEST'} or x.get('conflicts')]
        _print({'status':'PASS' if not bad else 'REVIEW_REQUIRED','results':results}); return 0 if not bad else 2
    if args.cmd=='propose-scope':
        safe=''.join(c if c.isalnum() or c in '-_' else '-' for c in args.path.strip('/')) or 'scope'
        path=root/'docs/proposals'/f'SCOPE-{safe}.md'
        path.write_text(f'# Scope Proposal — {args.path}\n\nStatus: PROPOSED\n\n## Objective\n{args.objective}\n\n## Effect\nNo canonical scope or implementation authority has been created. OWNER promotion is required.\n',encoding='utf-8',newline='\n')
        audit_append(root,'scope_proposed',details={'scope':args.path,'proposal':path.relative_to(root).as_posix()}); _print({'status':'PROPOSED','proposal':path.relative_to(root).as_posix()}); return 0
    return 1
