from __future__ import annotations
from pathlib import Path
from .utils import read_json

GENERATED = [
 'AGENTS.md','CLAUDE.md','GEMINI.md','CONVENTIONS.md',
 '.cursor/rules/00-governance.mdc','.github/copilot-instructions.md',
 '.windsurf/rules/00-governance.md','.aider.conf.yml'
]

def _render(template: str, **kw):
    for k,v in kw.items(): template=template.replace('{{'+k+'}}',v)
    return template

def expected(root: Path):
    behavior=(root/'.mda/source/behavior.mda.md').read_text(encoding='utf-8').strip()
    t=root/'.mda/templates'
    out={}
    for target,tpl in [
      ('AGENTS.md','AGENTS.md.tpl'),('CLAUDE.md','CLAUDE.md.tpl'),('GEMINI.md','GEMINI.md.tpl'),
      ('CONVENTIONS.md','CONVENTIONS.md.tpl'),('.cursor/rules/00-governance.mdc','cursor-governance.mdc.tpl'),
      ('.github/copilot-instructions.md','copilot-instructions.md.tpl'),('.windsurf/rules/00-governance.md','windsurf-governance.md.tpl')]:
        out[target]=_render((t/tpl).read_text(encoding='utf-8'),BEHAVIOR=behavior)
    out['.aider.conf.yml'] = 'read: CONVENTIONS.md\nauto-commits: false\ndirty-commits: false\n'
    folders=read_json(root/'.mda/source/folders.mda.json')['folders']
    ft=(t/'folder-agents.md.tpl').read_text(encoding='utf-8')
    for folder,spec in folders.items():
        forbid='\n'.join('- '+x for x in spec.get('forbid',[])) or '- none declared'
        out[f'{folder}/AGENTS.md']=_render(ft,FOLDER=folder,PURPOSE=spec['purpose'],WRITE_POLICY=spec['write_policy'],FORBID=forbid,INTENT_ID=spec.get('intent_id','N/A'),INTENT_SOURCE=spec.get('intent_source','N/A'))
        if spec.get('scope_class') == 'PRODUCT':
            import json
            out[f'{folder}/SCOPE_STATE.json'] = json.dumps({
                'scope': folder, 'scope_class': 'PRODUCT', 'state': spec.get('state','DECLARED_UNMATERIALIZED'),
                'objective': spec['purpose'], 'write_policy': spec['write_policy'],
                'intent_id': spec.get('intent_id'), 'intent_source': spec.get('intent_source')
            }, indent=2, ensure_ascii=False) + '\n'
    # Gemini can be configured to consume canonical AGENTS.md directly.
    out['.gemini/settings.json'] = '{\n  "context": {\n    "fileName": ["AGENTS.md"]\n  }\n}\n'
    return out

def compile_all(root: Path):
    out=expected(root)
    for rel,content in out.items():
        p=root/rel; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(content if content.endswith('\n') else content+'\n',encoding='utf-8',newline='\n')
    return sorted(out)

def drift(root: Path):
    bad=[]
    for rel,content in expected(root).items():
        p=root/rel
        expected_text=content if content.endswith('\n') else content+'\n'
        if not p.exists(): bad.append((rel,'MISSING'))
        elif p.read_text(encoding='utf-8') != expected_text: bad.append((rel,'DRIFT'))
    return bad
