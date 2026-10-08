import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'.scripts/repoctl.py'
class RepoCtlTests(unittest.TestCase):
    def run_cmd(self,*args):
        return subprocess.run([sys.executable,str(SCRIPT),*args],cwd=ROOT,text=True,capture_output=True)
    def test_verify_fast(self):
        p=self.run_cmd('verify','--fast'); self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    def test_compile_check(self):
        p=self.run_cmd('compile','--check'); self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    def test_context_contains_root_and_local(self):
        p=self.run_cmd('context','docs'); self.assertEqual(p.returncode,0,p.stderr)
        data=json.loads(p.stdout); self.assertIn('AGENTS.md',data['instruction_files']); self.assertIn('docs/AGENTS.md',data['instruction_files'])
    def test_capabilities_are_exactly_1_to_19(self):
        data=json.loads((ROOT/'.mda/source/capability-map.mda.json').read_text())
        self.assertEqual(sorted(x['point'] for x in data['capabilities']),list(range(1,20)))
    def test_advanced_capabilities_not_enabled_by_default(self):
        data=json.loads((ROOT/'.mda/source/capability-map.mda.json').read_text())
        states={x['point']:x['default_state'] for x in data['capabilities']}
        self.assertEqual(states[16],'DECLARED'); self.assertEqual(states[17],'DECLARED'); self.assertEqual(states[18],'DECLARED')
if __name__=='__main__': unittest.main()
