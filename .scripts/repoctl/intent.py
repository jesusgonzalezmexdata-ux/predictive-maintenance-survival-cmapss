from __future__ import annotations
from pathlib import Path
import hashlib, json, re, unicodedata
from .utils import read_json, write_json, rel, utcnow
from .adapters import compile_all

SECTION_MAP = {
    'vision': 'vision',
    'objective': 'objective', 'objectives': 'objective', 'objetivo': 'objective', 'objetivos': 'objective', 'ziel': 'objective', 'ziele': 'objective',
    'scope': 'scope', 'alcance': 'scope', 'umfang': 'scope',
    'constraints': 'constraints', 'restricciones': 'constraints', 'limitaciones': 'constraints', 'rahmenbedingungen': 'constraints', 'einschrankungen': 'constraints',
    'deliverables': 'deliverables', 'entregables': 'deliverables', 'resultados esperados': 'deliverables', 'liefergegenstande': 'deliverables',
    'acceptance criteria': 'acceptance_criteria', 'acceptance': 'acceptance_criteria', 'criterios de aceptacion': 'acceptance_criteria', 'aceptacion': 'acceptance_criteria', 'akzeptanzkriterien': 'acceptance_criteria',
    'non-goals': 'non_goals', 'non goals': 'non_goals', 'out of scope': 'non_goals', 'no objetivos': 'non_goals', 'fuera de alcance': 'non_goals', 'nicht-ziele': 'non_goals', 'nicht ziele': 'non_goals',
}

METADATA_ALIASES = {
    'tipo_intencion': 'intent_type', 'tipo_de_intencion': 'intent_type', 'intent_type': 'intent_type',
    'tipo_proyecto': 'project_kind', 'tipo_de_proyecto': 'project_kind', 'project_kind': 'project_kind',
    'destino': 'target', 'target': 'target',
    'materializacion': 'materialization', 'materialization': 'materialization',
    'objetivo': 'objective', 'objective': 'objective',
    'vision': 'vision', 'name': 'name', 'nombre': 'name'
}

INTENT_CLASS_ALIASES = {
    'PROJECT':'PROJECT','PROYECTO':'PROJECT','PROJEKT':'PROJECT',
    'DOMAIN':'DOMAIN','DOMINIO':'DOMAIN','DOMANE':'DOMAIN','DOMAENE':'DOMAIN',
    'FEATURE':'FEATURE','FUNCIONALIDAD':'FEATURE','FUNKTION':'FEATURE',
    'RESEARCH':'RESEARCH','INVESTIGACION':'RESEARCH','FORSCHUNG':'RESEARCH'
}

def _norm_label(text: str) -> str:
    text=unicodedata.normalize('NFKD',text)
    text=''.join(c for c in text if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',text.strip().lower())

LIST_FIELDS = {'scope','constraints','deliverables','acceptance_criteria','non_goals'}
KIND_ALIASES = {
    'DS': 'DATA_SCIENCE', 'DATA SCIENCE': 'DATA_SCIENCE', 'DATA_SCIENCE': 'DATA_SCIENCE',
    'API': 'API', 'CLI': 'CLI', 'WEB': 'WEB_APP', 'WEB APP': 'WEB_APP', 'WEB_APP': 'WEB_APP',
    'LIBRARY': 'LIBRARY', 'RESEARCH': 'RESEARCH', 'INFRA': 'INFRASTRUCTURE', 'INFRASTRUCTURE': 'INFRASTRUCTURE',
    'GENERIC': 'GENERIC', 'GENERICO': 'GENERIC',
    'CIENCIA DE DATOS':'DATA_SCIENCE', 'ANALITICA':'DATA_SCIENCE',
    'APLICACION WEB':'WEB_APP', 'BIBLIOTECA':'LIBRARY', 'INVESTIGACION':'RESEARCH', 'INFRAESTRUCTURA':'INFRASTRUCTURE'
}

def _slug(text: str) -> str:
    text=unicodedata.normalize('NFKD',text)
    text=''.join(c for c in text if not unicodedata.combining(c))
    s = re.sub(r'[^a-zA-Z0-9]+', '-', text.strip()).strip('-').lower()
    return s[:64] or 'intent'

def _split_items(lines):
    items=[]; paragraph=[]
    def flush():
        if paragraph:
            text=' '.join(x.strip() for x in paragraph if x.strip()).strip()
            if text: items.append(text)
            paragraph.clear()
    for line in lines:
        s=line.strip()
        if not s: flush(); continue
        m=re.match(r'^[-*+]\s+(.*)$',s) or re.match(r'^\d+[.)]\s+(.*)$',s)
        if m:
            flush(); items.append(m.group(1).strip())
        else:
            paragraph.append(s)
    flush(); return items

def parse_markdown(path: Path):
    text=path.read_text(encoding='utf-8')
    lines=text.splitlines()
    title=''
    metadata={}
    sections={}
    current=None
    in_fence=False
    for line in lines:
        if re.match(r'^\s*```', line):
            in_fence=not in_fence
            if current is not None: sections[current].append(line)
            continue
        if not in_fence:
            if not title:
                m=re.match(r'^#\s+(.+?)\s*$',line)
                if m: title=m.group(1).strip()
            h=re.match(r'^##\s+(.+?)\s*$',line)
            if h:
                label=_norm_label(h.group(1))
                key=SECTION_MAP.get(label,label.replace(' ','_'))
                current=key; sections.setdefault(current,[]); continue
            kv=re.match(r'^([\w][\w _-]{1,40}):\s*(.+?)\s*$',line,re.UNICODE)
            if kv and current is None:
                raw_key=_norm_label(kv.group(1)).replace(' ','_').replace('-','_')
                metadata[METADATA_ALIASES.get(raw_key,raw_key)]=kv.group(2).strip()
                continue
        if current is not None:
            sections[current].append(line)
    def section_text(name):
        return '\n'.join(x.rstrip() for x in sections.get(name,[])).strip()
    def section_list(name):
        return _split_items(sections.get(name,[]))
    objective=section_text('objective') or metadata.get('objective','')
    vision=section_text('vision') or metadata.get('vision','')
    if not objective and vision: objective=vision
    parsed={
        'title': title or metadata.get('name') or path.stem.replace('_',' ').replace('-',' ').strip(),
        'objective': objective,
        'vision': vision,
        'scope': section_list('scope'),
        'constraints': section_list('constraints'),
        'deliverables': section_list('deliverables'),
        'acceptance_criteria': section_list('acceptance_criteria'),
        'non_goals': section_list('non_goals'),
        'metadata': metadata,
        'raw_text': text,
    }
    return parsed

def _infer_kind(parsed):
    explicit=_norm_label(parsed['metadata'].get('project_kind','')).upper().replace('-',' ').strip()
    if explicit:
        return KIND_ALIASES.get(explicit, explicit.replace(' ','_'))
    blob=' '.join([parsed['title'],parsed['objective'],parsed['vision'],*parsed['scope']]).lower()
    tests=[
        ('DATA_SCIENCE',['data science','machine learning','mlops','model','dataset','analytics','analítica','ciencia de datos']),
        ('API',[' api ','endpoint','rest','graphql','service']),
        ('CLI',[' cli ','command line','terminal command']),
        ('WEB_APP',['web app','frontend','website','browser','web application']),
        ('LIBRARY',['library','sdk','package','reusable module']),
        ('RESEARCH',['research','investigation','hypothesis','experiment','investigación','hipótesis']),
        ('INFRASTRUCTURE',['infrastructure','terraform','kubernetes','deployment platform','infraestructura'])
    ]
    padded=' '+blob+' '
    for kind,needles in tests:
        if any(n in padded for n in needles): return kind
    return 'GENERIC'

def _infer_class(parsed, source: Path, root: Path):
    explicit=_norm_label(parsed['metadata'].get('intent_type','')).upper().replace(' ','_')
    explicit=INTENT_CLASS_ALIASES.get(explicit,INTENT_CLASS_ALIASES.get(explicit.replace('_',' '),explicit))
    if explicit in {'PROJECT','DOMAIN','FEATURE','RESEARCH'}: return explicit
    if _infer_kind(parsed)=='RESEARCH': return 'RESEARCH'
    try: src_rel=source.resolve().relative_to(root.resolve())
    except ValueError: src_rel=source
    if src_rel.parts and src_rel.parts[0]=='intake': return 'PROJECT'
    blob=(' '+parsed['title']+' '+parsed['objective']).lower()
    if 'feature' in blob or 'funcionalidad' in blob: return 'FEATURE'
    return 'DOMAIN'

def _default_target(parsed, source: Path, root: Path, intent_class: str):
    explicit=parsed['metadata'].get('target','').strip()
    if explicit: return explicit.strip('/\\') or '.'
    try: src_rel=source.resolve().relative_to(root.resolve())
    except ValueError: return '.'
    if src_rel.parts and src_rel.parts[0]=='intake': return '.'
    parent=src_rel.parent.as_posix()
    return parent if parent not in {'','.'} else '.'

def normalize(root: Path, source: Path):
    source=(root/source).resolve() if not source.is_absolute() else source.resolve()
    if not source.exists() or source.suffix.lower()!='.md':
        raise ValueError('Intent source must be an existing Markdown file.')
    try: source_rel=source.relative_to(root.resolve()).as_posix()
    except ValueError: raise ValueError('Intent source must be inside the repository.')
    parsed=parse_markdown(source)
    intent_class=_infer_class(parsed,source,root)
    kind=_infer_kind(parsed)
    target=_default_target(parsed,source,root,intent_class)
    digest=hashlib.sha256(parsed['raw_text'].encode('utf-8')).hexdigest()
    intent_id='INTENT-'+digest[:12].upper()
    missing=[]
    if not parsed['title'].strip(): missing.append('title_or_name')
    if not parsed['objective'].strip(): missing.append('objective_or_vision')
    recommended=[]
    for key in ['constraints','deliverables','acceptance_criteria','non_goals']:
        if not parsed[key]: recommended.append(key)
    state='NEEDS_DECISION' if missing else 'NORMALIZED'
    return {
        'schema_version':'2.0.0', 'intent_id':intent_id, 'source':source_rel,
        'intent_class':intent_class, 'project_kind':kind, 'title':parsed['title'].strip(),
        'objective':parsed['objective'].strip(), 'vision':parsed['vision'].strip(), 'target':target,
        'scope':parsed['scope'], 'constraints':parsed['constraints'], 'deliverables':parsed['deliverables'],
        'acceptance_criteria':parsed['acceptance_criteria'], 'non_goals':parsed['non_goals'],
        'missing_decisions':missing, 'recommended_missing':recommended,
        'content_hash':digest, 'state':state, 'ingested_at':utcnow(),
        'materialization':parsed['metadata'].get('materialization','SCAFFOLD_ONLY').upper().replace('-','_')
    }

def _join_target(target: str, child: str):
    t=target.strip('/\\')
    if t in {'','.'}: return child.strip('/\\')
    c=child.strip('/\\')
    return f'{t}/{c}' if c else t

def _architecture_markdown(contract, profile, scopes):
    lines=[
        f"# Architecture Proposal — {contract['title']}", '',
        f"Status: **{'NEEDS_DECISION' if contract['missing_decisions'] else 'ARCHITECTURE_PROPOSED'}**", '',
        f"Intent: `{contract['intent_id']}`", f"Source: `{contract['source']}`", f"Class: `{contract['intent_class']}`", f"Project kind: `{contract['project_kind']}`", '',
        '## Objective','',contract['objective'] or '_Missing: objective or vision must be supplied._','',
        '## Architecture profile','',profile.get('description',''),'',
        '## Proposed governed scopes',''
    ]
    for path,purpose in scopes.items(): lines.append(f'- `{path}` — {purpose}')
    lines += ['', '## Governance behavior','',
              '- Every materialized scope receives a local `AGENTS.md` and `SCOPE_STATE.json`.',
              '- The intent layer may scaffold topology/specification but does not generate product implementation.',
              '- Missing decisions remain explicit and block claims of implementation readiness.',
              '- Any agent entering a scope resolves root + nearest local contract before effectful work.', '',
              '## Constraints']
    lines += [''] + ([f'- {x}' for x in contract['constraints']] or ['- No additional constraints were declared; do not invent them.'])
    lines += ['', '## Acceptance criteria',''] + ([f'- {x}' for x in contract['acceptance_criteria']] or ['- Acceptance criteria are not yet declared; implementation readiness remains incomplete.'])
    return '\n'.join(lines)+'\n'

def _spec_markdown(contract, scopes):
    lines=[f"# Bootstrap Specification — {contract['title']}",'',f"Spec ID: `SPEC-{contract['intent_id'][7:]}`",f"Derived from: `{contract['intent_id']}`",'','## Problem / objective','',contract['objective'] or '_Decision required._','', '## Required repository outcome','']
    lines += [f'- Declare governed scope `{x}`.' for x in scopes]
    lines += ['- Generate tool adapters from canonical MDA.', '- Preserve `CORE_CONTRACT != TOOL_ADAPTER`.', '- Keep product implementation absent until governed tasks exist.', '', '## Deliverables','']
    lines += ([f'- {x}' for x in contract['deliverables']] or ['- Architecture scaffold, contracts, bootstrap spec and initial work package.'])
    lines += ['', '## Acceptance criteria',''] + ([f'- {x}' for x in contract['acceptance_criteria']] or ['- BLOCKED_FOR_IMPLEMENTATION until owner supplies measurable acceptance criteria.'])
    lines += ['', '## Non-goals',''] + ([f'- {x}' for x in contract['non_goals']] or ['- No undeclared product behavior may be inferred from this bootstrap specification.'])
    return '\n'.join(lines)+'\n'

def _decisions_markdown(contract):
    missing=contract['missing_decisions'] + contract['recommended_missing']
    lines=[f"# Decisions Required — {contract['title']}",'',f"Intent: `{contract['intent_id']}`",'', 'The repository can preserve and scaffold the declared intent, but the following semantics are missing or recommended before implementation:','']
    lines += [f'- {x}' for x in missing] if missing else ['- None.']
    lines += ['', 'These gaps must not be filled by an agent as if they were owner decisions.']
    return '\n'.join(lines)+'\n'

def _profile_scopes(root: Path, contract):
    profiles=read_json(root/'.mda/source/scaffold-profiles.mda.json')['profiles']
    profile=profiles.get(contract['project_kind'],profiles['GENERIC'])
    if contract['intent_class'] in {'DOMAIN','FEATURE'}:
        target=contract['target'] if contract['target'] not in {'','.'} else _slug(contract['title'])
        return profile, {target: contract['objective'] or f"Governed scope for {contract['title']}."}
    scopes={_join_target(contract['target'],p):purpose for p,purpose in profile['scopes'].items()}
    return profile,scopes

def _write_bundle(root: Path, contract, profile, scopes):
    out=root/'docs/intents'/contract['intent_id']
    out.mkdir(parents=True,exist_ok=True)
    write_json(out/'INTENT_CONTRACT.json',contract)
    (out/'ARCHITECTURE_PROPOSAL.md').write_text(_architecture_markdown(contract,profile,scopes),encoding='utf-8',newline='\n')
    (out/'BOOTSTRAP_SPEC.md').write_text(_spec_markdown(contract,scopes),encoding='utf-8',newline='\n')
    (out/'DECISIONS_REQUIRED.md').write_text(_decisions_markdown(contract),encoding='utf-8',newline='\n')
    tasks=[
      {'id':'T-INTENT-001','role':'A6_PLANNER','action':'Review normalized intent, unresolved decisions and proposed topology.','effect':'PROPOSE_ONLY'},
      {'id':'T-INTENT-002','role':'A1_ORCHESTRATOR','action':'Route approved bootstrap work using minimum necessary context.','effect':'PROPOSE_ONLY'},
      {'id':'T-INTENT-003','role':'A4_TDD_GUIDE','action':'Begin product implementation only after a governed feature/task and measurable acceptance criteria exist.','effect':'BLOCKED_UNTIL_TASK_AUTHORITY'}
    ]
    write_json(out/'WORK_PACKAGE.json',{'schema_version':'2.0.0','intent_id':contract['intent_id'],'status':'READY_FOR_PLANNING' if not contract['missing_decisions'] else 'NEEDS_DECISION','tasks':tasks})
    return out

def _materialize_scopes(root: Path, contract, scopes, previous_intent_id=None):
    folders=read_json(root/'.mda/source/folders.mda.json')
    conflicts=[]; created=[]
    for path,purpose in scopes.items():
        if path in folders['folders']:
            existing=folders['folders'][path]
            owner_ids={contract['intent_id']}
            if previous_intent_id: owner_ids.add(previous_intent_id)
            if existing.get('scope_class')=='PRODUCT' and existing.get('intent_id') not in owner_ids:
                conflicts.append(path); continue
            if existing.get('scope_class')=='GOVERNANCE':
                # Governance path may be referenced by a profile (e.g. test/product nested); parent remains governance.
                continue
        folders['folders'][path]={
            'purpose':purpose,'write_policy':'APPROVED_TASK','forbid':['secrets','writes outside approved task scope','implementation without governed task'],
            'scope_class':'PRODUCT','state':'DECLARED_UNMATERIALIZED','intent_id':contract['intent_id'],'intent_source':contract['source']
        }
        created.append(path)
    if conflicts:
        return created,conflicts
    write_json(root/'.mda/source/folders.mda.json',folders)
    compile_all(root)
    return created,[]

def _update_project(root: Path, contract):
    if contract['intent_class'] not in {'PROJECT','RESEARCH'}: return False
    project=read_json(root/'config/project.json')
    if project.get('repository_mode')=='MASTER_TEMPLATE':
        project.update({'project_name':contract['title'],'objective':contract['objective'],'project_kind':contract['project_kind'],'repository_mode':'PROJECT','implementation_authority':'TASK_SCOPED','origin_intent':contract['intent_id']})
        write_json(root/'config/project.json',project); return True
    return False

def ingest(root: Path, source: Path, materialize=True):
    contract=normalize(root,source)
    registry=read_json(root/'config/intake-registry.json')
    previous=registry.get('entries',{}).get(contract['source'])
    previous_intent_id=previous.get('intent_id') if previous else None
    if previous_intent_id and previous_intent_id != contract['intent_id']:
        contract['previous_intent_id']=previous_intent_id
    profile,scopes=_profile_scopes(root,contract)
    out=_write_bundle(root,contract,profile,scopes)
    created=[]; conflicts=[]; project_updated=False
    if materialize and not contract['missing_decisions']:
        created,conflicts=_materialize_scopes(root,contract,scopes,previous_intent_id=previous_intent_id)
        if not conflicts:
            project_updated=_update_project(root,contract)
            contract['state']='SCAFFOLDED'
            write_json(out/'INTENT_CONTRACT.json',contract)
    registry=read_json(root/'config/intake-registry.json')
    registry['entries'][contract['source']]={
        'intent_id':contract['intent_id'],'content_hash':contract['content_hash'],'state':contract['state'],
        'last_ingested_at':utcnow(),'artifact_root':out.relative_to(root).as_posix(),'conflicts':conflicts
    }
    write_json(root/'config/intake-registry.json',registry)
    return {'contract':contract,'artifact_root':out.relative_to(root).as_posix(),'scopes_created':created,'conflicts':conflicts,'project_updated':project_updated}

def _has_top_level_marker(path: Path):
    in_fence=False
    try: lines=path.read_text(encoding='utf-8').splitlines()
    except Exception: return False
    for line in lines:
        if re.match(r'^\s*```',line):
            in_fence=not in_fence; continue
        if not in_fence and re.match(r'^\s*MDA-Intent:\s*true\s*$',line,re.I): return True
    return False

def discover(root: Path):
    cfg=read_json(root/'config/intake.json')
    found=[]
    inbox=root/cfg['inbox']
    inbox_excluded={'README.md','OBJECTIVE_TEMPLATE.md','AGENTS.md'}
    recognized=set(cfg.get('recognized_names',[]))
    if inbox.exists():
        for p in inbox.rglob('*.md'):
            rp=p.relative_to(root).as_posix()
            if '/examples/' in '/'+rp or p.name in inbox_excluded: continue
            found.append(rp)
    excluded_dirs={'.mda','.agents','.hooks','.logs','.sandbox','.scripts','.federated','.github','.cursor','.gemini','.windsurf','docs','config','test','intake','.git'}
    excluded_root_files={'README.md','AGENTS.md','CLAUDE.md','GEMINI.md','CONVENTIONS.md','SECURITY.md','CHANGELOG.md'}
    for first in root.iterdir():
        if first.name in excluded_dirs or (first.is_file() and first.name in excluded_root_files): continue
        candidates=[first] if first.is_file() else first.rglob('*.md')
        for p in candidates:
            if not p.is_file() or p.suffix.lower()!='.md': continue
            if p.name in recognized or _has_top_level_marker(p): found.append(p.relative_to(root).as_posix())
    return sorted(set(found))

def reconcile(root: Path, materialize=True):
    registry=read_json(root/'config/intake-registry.json')
    results=[]
    for source in discover(root):
        path=root/source
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        old=registry['entries'].get(source)
        if old and old.get('content_hash')==digest:
            results.append({'source':source,'status':'UNCHANGED','intent_id':old.get('intent_id')}); continue
        if old and old.get('content_hash')!=digest:
            results.append({'source':source,'status':'CHANGED_REQUIRES_EXPLICIT_REINGEST','intent_id':old.get('intent_id')}); continue
        try:
            r=ingest(root,path,materialize=materialize)
            results.append({'source':source,'status':'INGESTED','intent_id':r['contract']['intent_id'],'state':r['contract']['state'],'conflicts':r['conflicts']})
        except Exception as e:
            results.append({'source':source,'status':'ERROR','error':str(e)})
    return results
