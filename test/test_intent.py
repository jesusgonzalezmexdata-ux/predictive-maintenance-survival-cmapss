import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

SAMPLE='''# Test Analytics Project

MDA-Intent: true
Intent-Type: PROJECT
Project-Kind: DATA_SCIENCE
Target: .
Materialization: SCAFFOLD_ONLY

## Vision
Create reproducible analytics from manufacturing data.

## Objective
Build the governed repository architecture required for traceable analytics.

## Constraints
- No secrets in the repository.

## Deliverables
- Governed topology.

## Acceptance Criteria
- Repository remains GREENFIELD after architecture scaffolding.

## Non-Goals
- No product implementation during intake.
'''

def _host_project_state():
    # Read-only check (no audit entry), same rule as repoctl preflight.
    sys.path.insert(0,str(ROOT/'.scripts'))
    try:
        from repoctl.state import detect
        return detect(ROOT)['project_state']
    except Exception:
        return 'UNKNOWN'
    finally:
        sys.path.pop(0)

# These tests exercise the kernel's GREENFIELD intake bootstrap on a copy of this repository.
# Once the host project owns product scopes (BROWNFIELD), intake reports scope conflicts by design,
# so the scenario no longer applies. They still run on a pristine kernel template.
@unittest.skipUnless(_host_project_state()=='GREENFIELD','kernel greenfield-bootstrap tests do not apply to an instantiated (BROWNFIELD) project')
class IntentBootstrapTests(unittest.TestCase):
    def make_repo(self):
        td=tempfile.TemporaryDirectory()
        dst=Path(td.name)/'repo'
        shutil.copytree(ROOT,dst,ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc'))
        return td,dst

    def run_cmd(self,root,*args):
        return subprocess.run([sys.executable,str(root/'.scripts/repoctl.py'),*args],cwd=root,text=True,capture_output=True)

    def test_inbox_scaffolds_without_product_code(self):
        td,repo=self.make_repo()
        try:
            f=repo/'intake'/'test-project.md'; f.write_text(SAMPLE,encoding='utf-8')
            p=self.run_cmd(repo,'reconcile-intake')
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            data=json.loads(p.stdout)
            item=[x for x in data['results'] if x['source']=='intake/test-project.md'][0]
            self.assertEqual(item['status'],'INGESTED')
            intent=item['intent_id']
            self.assertTrue((repo/'docs/intents'/intent/'INTENT_CONTRACT.json').exists())
            self.assertTrue((repo/'src/AGENTS.md').exists())
            self.assertTrue((repo/'src/SCOPE_STATE.json').exists())
            self.assertFalse(any(p.suffix in {'.py','.ts','.js','.go','.rs'} for p in (repo/'src').rglob('*') if p.is_file()))
            inspect=self.run_cmd(repo,'inspect'); self.assertEqual(inspect.returncode,0,inspect.stdout+inspect.stderr)
            self.assertEqual(json.loads(inspect.stdout)['state']['project_state'],'GREENFIELD')
        finally: td.cleanup()

    def test_intent_change_is_not_silently_reconciled(self):
        td,repo=self.make_repo()
        try:
            f=repo/'intake'/'test-project.md'; f.write_text(SAMPLE,encoding='utf-8')
            first=self.run_cmd(repo,'reconcile-intake'); self.assertEqual(first.returncode,0,first.stdout+first.stderr)
            f.write_text(SAMPLE+'\n## Extra\nChanged owner intent.\n',encoding='utf-8')
            second=self.run_cmd(repo,'reconcile-intake')
            self.assertEqual(second.returncode,2,second.stdout+second.stderr)
            data=json.loads(second.stdout)
            item=[x for x in data['results'] if x['source']=='intake/test-project.md'][0]
            self.assertEqual(item['status'],'CHANGED_REQUIRES_EXPLICIT_REINGEST')
        finally: td.cleanup()

    def test_spanish_intent_is_normalized(self):
        td,repo=self.make_repo()
        try:
            f=repo/'intake'/'proyecto-es.md'
            f.write_text('''# Analítica Industrial\n\nMDA-Intent: true\nTipo-Intención: PROYECTO\nTipo-Proyecto: CIENCIA DE DATOS\n\n## Visión\nCrear evidencia industrial reproducible.\n\n## Objetivo\nConstruir una arquitectura gobernada para analítica.\n\n## Restricciones\n- Sin secretos.\n\n## Entregables\n- Arquitectura.\n\n## Criterios de aceptación\n- Contratos locales generados.\n\n## No objetivos\n- No desplegar a producción.\n''',encoding='utf-8')
            p=self.run_cmd(repo,'reconcile-intake'); self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            item=[x for x in json.loads(p.stdout)['results'] if x['source']=='intake/proyecto-es.md'][0]
            contract=json.loads((repo/'docs/intents'/item['intent_id']/'INTENT_CONTRACT.json').read_text())
            self.assertEqual(contract['intent_class'],'PROJECT')
            self.assertEqual(contract['project_kind'],'DATA_SCIENCE')
            self.assertTrue(contract['acceptance_criteria'])
            self.assertEqual(contract['missing_decisions'],[])
        finally: td.cleanup()

    def test_master_readme_code_example_is_not_discovered(self):
        td,repo=self.make_repo()
        try:
            p=self.run_cmd(repo,'discover-intents'); self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            data=json.loads(p.stdout)
            self.assertNotIn('README.md',data['sources'])
            self.assertNotIn('intake/AGENTS.md',data['sources'])
        finally: td.cleanup()

    def test_marked_markdown_in_future_folder_is_discovered(self):
        td,repo=self.make_repo()
        try:
            future=repo/'domains'/'quality'; future.mkdir(parents=True)
            f=future/'quality-objective.md'
            f.write_text('''# Quality Domain\n\nMDA-Intent: true\nIntent-Type: DOMAIN\n\n## Objective\nCreate a governed quality-analysis domain.\n\n## Acceptance Criteria\n- Local contract exists before implementation.\n''',encoding='utf-8')
            d=self.run_cmd(repo,'discover-intents'); self.assertEqual(d.returncode,0,d.stdout+d.stderr)
            self.assertIn('domains/quality/quality-objective.md',json.loads(d.stdout)['sources'])
            r=self.run_cmd(repo,'reconcile-intake'); self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertTrue((future/'AGENTS.md').exists())
            inspect=self.run_cmd(repo,'inspect'); self.assertEqual(json.loads(inspect.stdout)['state']['project_state'],'GREENFIELD')
        finally: td.cleanup()

    def test_explicit_reingest_updates_owned_scopes(self):
        td,repo=self.make_repo()
        try:
            f=repo/'intake'/'test-project.md'; f.write_text(SAMPLE,encoding='utf-8')
            first=self.run_cmd(repo,'reconcile-intake'); self.assertEqual(first.returncode,0,first.stdout+first.stderr)
            before=json.loads((repo/'src/SCOPE_STATE.json').read_text())['intent_id']
            changed=SAMPLE.replace('traceable analytics.','traceable and reviewable analytics.')
            f.write_text(changed,encoding='utf-8')
            second=self.run_cmd(repo,'ingest','intake/test-project.md')
            self.assertEqual(second.returncode,0,second.stdout+second.stderr)
            after=json.loads((repo/'src/SCOPE_STATE.json').read_text())['intent_id']
            self.assertNotEqual(before,after)
            data=json.loads(second.stdout)
            self.assertEqual(data['conflicts'],[])
            self.assertEqual(data['contract']['previous_intent_id'],before)
        finally: td.cleanup()

    def test_missing_objective_surfaces_decision(self):
        td,repo=self.make_repo()
        try:
            f=repo/'intake'/'incomplete.md'; f.write_text('# Incomplete\n\nMDA-Intent: true\nIntent-Type: PROJECT\n',encoding='utf-8')
            p=self.run_cmd(repo,'ingest','intake/incomplete.md')
            self.assertEqual(p.returncode,2,p.stdout+p.stderr)
            data=json.loads(p.stdout)
            self.assertEqual(data['contract']['state'],'NEEDS_DECISION')
            self.assertIn('objective_or_vision',data['contract']['missing_decisions'])
            self.assertEqual(data['scopes_created'],[])
        finally: td.cleanup()

if __name__=='__main__': unittest.main()
