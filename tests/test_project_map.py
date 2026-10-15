import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from reqcontext.project_map import ProjectMap


class ProjectMapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.root.mkdir()
        (self.root / 'src').mkdir()
        (self.root / 'src/service.py').write_text('def send():\n    return 1\n')
        (self.root / 'README.md').write_text('A small upload service.')
        self.map = ProjectMap(self.root, cache=Path(self.temp.name) / 'map.json')

    def test_build_reuse_and_explicit_refresh(self):
        self.assertFalse(self.map.build()['reused'])
        (self.root / 'new').mkdir()
        with patch('os.walk', side_effect=AssertionError('unexpected traversal')):
            self.assertTrue(self.map.build()['reused'])
            self.assertNotIn('new', self.map.load()['folders'])
        self.map.build(refresh=True)
        self.assertIn('new', self.map.load()['folders'])

    def test_hidden_generated_and_symlink_directories_are_omitted(self):
        for name in ['.private', 'node_modules']:
            (self.root / name).mkdir()
        (self.root / 'link').symlink_to(self.root / 'src', target_is_directory=True)
        self.assertEqual(set(self.map.build()['map']['folders']), {'.', 'src'})

    def test_model_summary_reused_and_invalid_refresh_rolls_back(self):
        calls=[]
        def model(payload):
            calls.append(payload)
            return {'description':'Source-backed description.', 'evidence':list(payload['samples'])[:1]}
        self.map.build(model=model)
        self.map.build(refresh=True, model=model)
        self.assertEqual(len(calls),2)
        original=self.map.cache.read_bytes()
        (self.root / 'src/service.py').write_text('def receive():\n    return 2\n')
        with self.assertRaises(ValueError):
            self.map.build(refresh=True, model=lambda _: {'description':'Invented','evidence':['missing.py']})
        self.assertEqual(self.map.cache.read_bytes(),original)

    def test_three_fresh_processes_never_read_project_files(self):
        self.map.build()
        script='''
import sys
from pathlib import Path
from unittest.mock import patch
from reqcontext.project_map import ProjectMap
root=Path(sys.argv[1]); original=Path.open

def guarded_open(path,*args,**kwargs):
    if path.is_relative_to(root): raise AssertionError('source read')
    return original(path,*args,**kwargs)
with patch('os.walk',side_effect=AssertionError('source scan')), patch.object(Path,'open',guarded_open):
    project=ProjectMap(root,cache=sys.argv[2])
    assert project.describe('src')['files']==['service.py']
    print(project.overview())
'''
        for _ in range(3):
            output=subprocess.check_output([sys.executable,'-c',script,str(self.root),str(self.map.cache)],text=True)
            self.assertIn('small upload service',output)

    def test_map_does_not_change_repository(self):
        before=sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        self.map.build()
        self.assertEqual(before,sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*')))
        with self.assertRaises(ValueError): ProjectMap(self.root,cache=self.root/'map.json')

    def test_missing_map_is_actionable_and_overview_bounded(self):
        with self.assertRaisesRegex(ValueError,'build'): self.map.load()
        for i in range(100): (self.root/f'component_{i}').mkdir()
        self.map.build()
        self.assertLessEqual(len(self.map.overview(max_chars=500)),500)

    def test_changed_revision_is_visible(self):
        self.map.build()
        with patch('reqcontext.project_map.revision',return_value='another-checkout'):
            self.assertIn('checkout revision changed',self.map.overview())

    def test_session_hook_injects_existing_map_and_tolerates_missing_map(self):
        from io import StringIO
        from reqcontext.session_hook import main
        event=json.dumps({'hook_event_name':'SessionStart','cwd':str(self.root)})
        with patch.dict(os.environ,{'XDG_CACHE_HOME':str(Path(self.temp.name)/'cache')}):
            output=StringIO()
            with patch('sys.stdin',StringIO(event)), patch('sys.stdout',output), patch('sys.stderr',StringIO()):
                self.assertEqual(main(),0)
            self.assertEqual(output.getvalue(),'')
            ProjectMap(self.root).build()
            output=StringIO()
            with patch('sys.stdin',StringIO(event)), patch('sys.stdout',output), patch('os.walk',side_effect=AssertionError('source scan')):
                self.assertEqual(main(),0)
            data=json.loads(output.getvalue())['hookSpecificOutput']
            self.assertEqual(data['hookEventName'],'SessionStart')
            self.assertIn('small upload service',data['additionalContext'])
