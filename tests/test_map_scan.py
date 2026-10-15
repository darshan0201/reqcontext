"""Behavioral tests for explicit full scans, deferred summaries and scope expansion."""
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from reqcontext.project_map import ProjectMap


class FullMapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.project = ProjectMap(self.root, cache=Path(self.temp.name) / 'map.json')
        self.calls = []

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def model(self, payload):
        self.calls.append(payload)
        return {'description': 'Mixed component responsibilities.',
                'evidence': list(payload['samples'])}

    def build(self, **kwargs):
        return self.project.build(mode='full', model=self.model, **kwargs)['map']

    def test_all_files_and_late_chunks_reach_model(self):
        for i in range(5):
            self.write(f'mixed/{i}.txt', str(i))
        self.write('mixed/late.txt', 'x' * 13000 + 'LATE_RESPONSIBILITY')
        data = self.build()
        self.assertEqual(data['coverage']['files_examined'], 6)
        source_payloads = '\n'.join(str(c['samples']) for c in self.calls)
        self.assertIn('LATE_RESPONSIBILITY', source_payloads)
        self.assertIn('mixed/4.txt', source_payloads)
        self.assertEqual(data['folders']['mixed']['kind'], 'model')

    def test_shared_dependency_and_signature_changes_bypass_threshold(self):
        self.write('automotive/bmw/car.py', 'from shared.diagnostics import check\n')
        self.write('automotive/mercedes/car.py', 'from shared.diagnostics import check\n')
        self.write('shared/diagnostics.py', 'def check():\n    return 1\n')
        self.build()
        related = self.project.related('shared')
        self.assertEqual(related['candidate_scope'], ['automotive/bmw', 'automotive/mercedes', 'shared'])
        self.assertTrue(all(e['line'] == 1 for e in related['evidence']))
        self.write('shared/diagnostics.py', 'def check():\n    return 2\n')
        data = self.build(refresh=True)
        self.assertIn('shared', data['refresh']['refreshed_components'])
        self.assertEqual(data['refresh']['affected_consumers'], ['automotive/bmw', 'automotive/mercedes'])
        self.write('isolated/api.py', 'def run():\n    pass\n')
        self.build(refresh=True)
        self.write('isolated/api.py', 'def run(required):\n    pass\n')
        self.assertIn('isolated', self.build(refresh=True)['refresh']['refreshed_components'])

    def test_changes_accumulate_against_summary_baseline(self):
        self.write('feature/a.txt', 'original')
        self.build(change_threshold=3)
        for name in ['b', 'c']:
            self.write(f'feature/{name}.txt', name)
            data = self.build(refresh=True, change_threshold=3)
            self.assertIn('feature', data['refresh']['pending_components'])
        self.assertEqual(len(data['folders']['feature']['pending_changes']), 2)
        self.write('feature/d.txt', 'd')
        data = self.build(refresh=True, change_threshold=3)
        self.assertIn('feature', data['refresh']['refreshed_components'])
        self.assertEqual(data['folders']['feature']['pending_changes'], [])

    def test_topology_build_files_and_deletion_bypass_threshold(self):
        self.write('feature/a.txt', 'a')
        self.build()
        self.write('feature/child/a.txt', 'a')
        self.assertIn('feature', self.build(refresh=True)['refresh']['refreshed_components'])
        self.write('feature/pyproject.toml', '[project]\nname="example"')
        self.assertIn('feature', self.build(refresh=True)['refresh']['refreshed_components'])
        (self.root / 'feature/a.txt').unlink()
        self.assertIn('feature', self.build(refresh=True)['refresh']['refreshed_components'])

    def test_failed_model_refresh_preserves_cache(self):
        self.write('api.py', 'def before(): pass')
        self.build()
        before = self.project.cache.read_bytes()
        self.write('api.py', 'def after(): pass')
        with self.assertRaises(ValueError):
            self.project.build(refresh=True, mode='full', model=lambda _: {'description': 'Wrong', 'evidence': ['missing']})
        self.assertEqual(before, self.project.cache.read_bytes())

    def test_coverage_reports_exclusions_and_parse_failure(self):
        self.write('bad.py', 'def !')
        self.write('large.txt', 'x' * 30)
        self.write('image.bin', 'binary')
        self.write('node_modules/dep.js', 'excluded')
        data = self.project.build(mode='full', max_file_bytes=20)['map']
        self.assertEqual(data['coverage']['parse_failures'], ['bad.py'])
        self.assertEqual({s['reason'] for s in data['coverage']['skipped']},
                         {'size limit', 'unsupported type', 'excluded directory or symlink'})

    def test_full_mode_is_opt_in_and_cache_reads_are_scan_free(self):
        self.write('api.py', 'def run(): pass')
        self.project.build()
        with self.assertRaisesRegex(ValueError, 'refresh'):
            self.build()
        self.build(refresh=True)
        with patch('os.walk', side_effect=AssertionError('unexpected scan')):
            self.assertTrue(self.project.build()['reused'])
            self.project.overview()
            self.project.describe()
            self.project.related()
        self.assertEqual(self.project.build(refresh=True)['map']['scan_mode'], 'full')

    def test_relative_imports_resolve_and_external_imports_do_not(self):
        self.write('src/pkg/client/api.py', 'from ..shared import helper\nimport external_dependency\n')
        self.write('src/pkg/shared/helper.py', 'def run(): pass')
        edges = self.build()['relationships']
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]['target'], 'src/pkg/shared/helper.py')

    def test_full_map_in_three_new_processes_reads_no_source(self):
        self.write('feature/api.py', 'def run(): pass')
        self.build()
        script = """
import sys
from pathlib import Path
from unittest.mock import patch
from reqcontext.project_map import ProjectMap
root = Path(sys.argv[1])
original = Path.open
def guarded_open(path, *args, **kwargs):
    if path.is_relative_to(root):
        raise AssertionError('source file read')
    return original(path, *args, **kwargs)
with patch('os.walk', side_effect=AssertionError('source traversal')), patch.object(Path, 'open', guarded_open):
    project = ProjectMap(root, cache=sys.argv[2])
    assert project.build()['source_files_read'] == 0
    assert project.describe('feature')['files'] == ['api.py']
    project.related('feature')
    print(project.overview())
"""
        for _ in range(3):
            result = subprocess.check_output([sys.executable, '-c', script, str(self.root), str(self.project.cache)], text=True)
            self.assertIn('Scan mode: full', result)
