import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reqcontext import RequirementContext, SourceDocument
from reqcontext.investigation import Investigator, validate_final
from reqcontext.mcp_server import SnapshotTools

class SnapshotDocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'repo';self.root.mkdir()
        (self.root/'src').mkdir()
        (self.root/'src/service.py').write_text('def upload(data):\n    return send(data)\n')
        (self.root/'src/helper.py').write_text('def send(data):\n    return data\n')
        self.cache=Path(self.temp.name)/'snapshot.db'
    def tearDown(self):
        self.temp.cleanup()
    def test_snapshot_analysis_never_calls_source_enumerator(self):
        with RequirementContext(self.root,cache=self.cache) as ctx:
            first=ctx.analyze('upload')
        with patch('reqcontext.index.Index.paths',side_effect=AssertionError('filesystem scan')):
            with RequirementContext(self.root,cache=self.cache) as ctx:
                again=ctx.analyze('upload')
        self.assertEqual(first.evidence,again.evidence)
        self.assertEqual(again.index_stats['source_files_read'],0)
        self.assertTrue(again.index_stats['snapshot_reused'])
    def test_stale_snapshot_only_updates_on_explicit_refresh(self):
        with RequirementContext(self.root,cache=self.cache) as ctx:
            old=ctx.analyze('upload')
            (self.root/'src/service.py').write_text('def upload(data):\n    return changed_send(data)\n')
            frozen=ctx.analyze('upload')
            self.assertEqual(old.evidence,frozen.evidence)
            ctx.refresh()
            fresh=ctx.analyze('upload')
            self.assertTrue(any('changed_send' in e['excerpt'] for e in fresh.evidence))
    def test_folder_scoped_search_excludes_other_folders(self):
        (self.root/'tests').mkdir()
        (self.root/'tests/test_upload.py').write_text('def test_upload():\n    upload()\n')
        with RequirementContext(self.root,cache=self.cache) as ctx:
            ctx.analyze('upload')
            hits=ctx.index.search('upload',prefix='src')
            self.assertTrue(hits)
            self.assertTrue(all(e['path'].startswith('src/') for e in hits))
            self.assertEqual(ctx.index.folder_map('')['folders'][0]['path'],'src')
    def test_neighbors_are_snapshot_name_matches(self):
        with RequirementContext(self.root,cache=self.cache) as ctx:
            brief=ctx.analyze('upload')
            i=Investigator(ctx,brief)
            caller=i.execute({'tool':'neighbors','path':'src/helper.py','symbol':'send'})
            self.assertEqual(caller['callers'][0]['symbol'],'upload')
            self.assertIn('not resolved',caller['note'])
    def test_external_text_revision_and_removal(self):
        doc=Path(self.temp.name)/'spec.txt';doc.write_text('Uploads require a size limit.\n')
        selected=SourceDocument(doc,title='Upload Spec',revision='2.1',source_type='specification')
        with RequirementContext(self.root,cache=self.cache,documents=[selected]) as ctx:
            brief=ctx.analyze('size limit')
            evidence=next(e for e in brief.evidence if e['kind']=='document')
            self.assertEqual(evidence['source']['revision'],'2.1')
            self.assertFalse(evidence['source']['classification_verified'])
            doc.write_text('Uploads require a different limit.\n')
            frozen=ctx.analyze('size limit')
            self.assertEqual(brief.evidence,frozen.evidence)
            ctx.refresh()
            self.assertTrue(any('different limit' in e['excerpt'] for e in ctx.analyze('limit').evidence))
        with RequirementContext(self.root,cache=self.cache) as ctx:
            ctx.refresh()
            self.assertFalse(any(e['kind']=='document' for e in ctx.analyze('limit').evidence))
    def test_pdf_page_local_lines_are_not_deduplicated(self):
        doc=Path(self.temp.name)/'spec.pdf';doc.write_bytes(b'fixture input bytes')
        fingerprint=hashlib.sha256(doc.read_bytes()).hexdigest()
        with patch('reqcontext.index.extract',return_value=(fingerprint,[(1,'uniquealpha requirement'),(2,'uniquebeta requirement')],[])):
            with RequirementContext(self.root,cache=self.cache,documents=[doc]) as ctx:
                ctx.index.ensure_snapshot()
                brief=ctx.analyze('no_match_zzqxv')
                i=Investigator(ctx,brief)
                key=SourceDocument(doc).key()
                i.execute({'tool':'read_document','path':key,'page':1})
                i.execute({'tool':'read_document','path':key,'page':2})
                self.assertEqual({e['page'] for e in brief.evidence},{1,2})
    def test_failed_reference_removes_obsolete_evidence(self):
        doc=Path(self.temp.name)/'spec.txt';doc.write_text('uniquerule limit')
        with RequirementContext(self.root,cache=self.cache,documents=[doc]) as ctx:
            self.assertTrue(any(e['kind']=='document' for e in ctx.analyze('uniquerule').evidence))
            doc.unlink();ctx.refresh()
            brief=ctx.analyze('uniquerule')
            self.assertFalse(brief.evidence)
            self.assertTrue(any('ingestion failed' in w for w in brief.warnings))
    def test_selected_folder_requires_evidence_in_that_folder(self):
        with RequirementContext(self.root,cache=self.cache) as ctx:
            brief=ctx.analyze('upload')
        response={'scope':[{'folder':'elsewhere','reason':'unfounded','evidence_ids':[brief.evidence[0]['id']]}]}
        with self.assertRaises(ValueError):
            validate_final(response,brief.evidence,brief.requirement)
    def test_mcp_tools_reuse_snapshot(self):
        tools=SnapshotTools(self.root,self.cache)
        tools.overview()
        with patch('reqcontext.index.Index.paths',side_effect=AssertionError('scan')):
            result=tools.lookup({'tool':'read_symbol','path':'src/service.py','symbol':'upload'})
        self.assertTrue(result['evidence'])
        self.assertEqual(result['snapshot']['files'],2)

    def test_snapshot_does_not_reextract_or_read_documents(self):
        doc=Path(self.temp.name)/'spec.txt';doc.write_text('document_unique_rule')
        with RequirementContext(self.root,cache=self.cache,documents=[doc]) as ctx:
            ctx.analyze('document_unique_rule')
        with patch('reqcontext.index.Index.paths',side_effect=AssertionError('scan')), patch('pathlib.Path.read_bytes',side_effect=AssertionError('document read')), patch('reqcontext.index.extract',side_effect=AssertionError('extract')):
            with RequirementContext(self.root,cache=self.cache,documents=[doc]) as ctx:
                brief=ctx.analyze('document_unique_rule')
        self.assertTrue(any(e['kind']=='document' for e in brief.evidence))

    def test_document_metadata_change_requires_refresh_and_updates_search(self):
        doc=Path(self.temp.name)/'spec.txt';doc.write_text('unchanged contents')
        a=SourceDocument(doc,title='Oldunique',revision='1')
        b=SourceDocument(doc,title='Newunique',revision='2')
        with RequirementContext(self.root,cache=self.cache,documents=[a]) as ctx:
            ctx.analyze('Oldunique')
        with RequirementContext(self.root,cache=self.cache,documents=[b]) as ctx:
            with self.assertRaises(ValueError):ctx.analyze('Newunique')
            ctx.refresh()
            evidence=next(e for e in ctx.analyze('Newunique').evidence if e['kind']=='document')
        self.assertEqual(evidence['source']['revision'],'2')

    def test_failed_refresh_rolls_back_whole_snapshot(self):
        with RequirementContext(self.root,cache=self.cache) as ctx:
            before=ctx.analyze('upload')
            snapshot=ctx.index.snapshot()
            (self.root/'src/service.py').write_text('def upload(data):\n    return altered(data)\n')
            with patch.object(ctx.index,'refresh_documents',side_effect=RuntimeError('injected refresh failure')):
                with self.assertRaises(RuntimeError):ctx.refresh()
            after=ctx.analyze('upload')
            self.assertEqual(before.evidence,after.evidence)
            self.assertEqual(snapshot,ctx.index.snapshot())
            ctx.refresh()
            self.assertTrue(any('altered' in e['excerpt'] for e in ctx.analyze('upload').evidence))

    def test_folder_wildcards_are_literal(self):
        folder=self.root/'src[legacy]';folder.mkdir()
        (folder/'upload.py').write_text('def upload(data):\n    return data\n')
        with RequirementContext(self.root,cache=self.cache) as ctx:
            ctx.analyze('upload')
            hits=ctx.index.search('upload',prefix='src[legacy]')
        self.assertTrue(hits)
        self.assertTrue(all(e['path'].startswith('src[legacy]/') for e in hits))

    def test_invalid_query_limits_are_rejected(self):
        with RequirementContext(self.root,cache=self.cache) as ctx:
            for limit in [0,-1,51,True]:
                with self.assertRaises(ValueError):ctx.index.search('upload',limit=limit)
            with self.assertRaises(ValueError):ctx.index.folder_map(limit=0)

    def test_symbol_fragment_lookup_respects_scope(self):
        with RequirementContext(self.root,cache=self.cache) as ctx:
            brief=ctx.analyze('upload')
            result=Investigator(ctx,brief).execute({'tool':'symbols','query':'upl','prefix':'src'})
        self.assertEqual(result['symbols'][0]['symbol'],'upload')

    def test_changed_source_size_policy_requires_refresh(self):
        with RequirementContext(self.root,cache=self.cache) as ctx:ctx.analyze('upload')
        with RequirementContext(self.root,cache=self.cache,max_file_bytes=100) as ctx:
            with self.assertRaises(ValueError):ctx.analyze('upload')
            ctx.refresh()
            self.assertTrue(ctx.analyze('upload').evidence)
