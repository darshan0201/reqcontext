import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from reqcontext import RequirementContext


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.write("uploads.py", "def background_upload(data):\n    return send(data)\n\ndef foreground_upload(data):\n    return send(data)\n")
        self.write("policy.md", "Upload retry policy: retry network timeouts for at most three attempts.\n")
        self.context = RequirementContext(self.root,refresh_mode="auto")

    def tearDown(self):
        self.context.close()
        self.temp.cleanup()

    def write(self, path, text):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
        return destination

    def test_grounding_and_scope_question(self):
        brief = self.context.analyze("Add retry support when upload fails")
        self.assertTrue(any(e["path"] == "uploads.py" for e in brief.evidence))
        self.assertTrue(any(e["path"] == "policy.md" for e in brief.evidence))
        self.assertEqual(brief.questions, [])
        self.assertEqual(brief.mode, "retrieval-only")
        self.assertEqual(brief.interpretations, [])

    def test_evidence_lines_match_source(self):
        for e in self.context.analyze("upload retry").evidence:
            lines = (self.root / e["path"]).read_text().splitlines()
            self.assertEqual(e["excerpt"], "\n".join(lines[e["start"] - 1:e["end"]]))
            self.assertEqual(len(e["hash"]), 64)

    def test_incremental_cache(self):
        first = self.context.analyze("upload")
        second = self.context.analyze("upload")
        self.assertEqual(first.index_stats["indexed"], 2)
        self.assertEqual(second.index_stats["indexed"], 0)
        self.assertEqual(second.index_stats["reused"], 2)
        self.assertEqual(first.evidence, second.evidence)

    def test_same_size_same_mtime_edit_detected(self):
        self.context.analyze("upload")
        path = self.root / "policy.md"
        info = path.stat()
        path.write_text(path.read_text().replace("three", "seven"))
        os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))
        brief = self.context.analyze("retry")
        self.assertEqual(brief.index_stats["indexed"], 1)
        self.assertTrue(any("seven" in e["excerpt"] for e in brief.evidence))

    def test_deletion_removes_search_results(self):
        self.context.analyze("upload")
        (self.root / "uploads.py").unlink()
        brief = self.context.analyze("upload")
        self.assertEqual(brief.index_stats["removed"], 1)
        self.assertFalse(any(e["path"] == "uploads.py" for e in brief.evidence))

    def test_decision_staleness_and_scope(self):
        self.context.remember(task="upload", question="Which path?", answer="background", sources=["uploads.py"])
        self.assertEqual(self.context.analyze("upload").decisions[0]["status"], "user_confirmed")
        self.assertEqual(self.context.analyze("unrelated task").decisions, [])
        self.write("uploads.py", "def upload():\n    pass\n")
        self.assertEqual(self.context.analyze("upload").decisions[0]["status"], "needs_review")

    def test_conflicting_decisions_exposed(self):
        for answer in ["yes", "no"]:
            self.context.remember(task="upload", question="Retry?", answer=answer)
        brief = self.context.analyze("upload")
        self.assertEqual(len(brief.decisions), 2)
        self.assertEqual(brief.questions, [])

    def test_missing_source_rejected(self):
        with self.assertRaises(ValueError):
            self.context.remember(task="x", question="x", answer="x", sources=["missing.py"])

    def test_hidden_generated_and_symlink_exclusion(self):
        self.write(".env", "upload secret")
        self.write("node_modules/vendor.py", "def upload_secret(): pass")
        self.write(".private/info.md", "upload secret")
        (self.root / "linked.py").symlink_to(self.root / "uploads.py")
        brief = self.context.analyze("upload secret")
        self.assertEqual(brief.index_stats["indexed"], 2)

    def test_custom_exclusions(self):
        with RequirementContext(self.root, excludes=["policy.*"],refresh_mode="auto") as context:
            brief = context.analyze("upload retry")
        self.assertFalse(any(e["path"] == "policy.md" for e in brief.evidence))

    def test_binary_oversize_and_bad_encoding(self):
        self.write("large.md", "upload " * 1000)
        (self.root / "binary.py").write_bytes(b"upload\0")
        (self.root / "bad.md").write_bytes(b"\xffupload")
        with RequirementContext(self.root, max_file_bytes=500,refresh_mode="auto") as context:
            brief = context.analyze("upload")
        self.assertEqual(brief.index_stats["skipped"], 3)

    def test_syntax_error_keeps_text_evidence(self):
        self.write("broken.py", "def upload(\n")
        brief = self.context.analyze("upload")
        self.assertTrue(any(e["path"] == "broken.py" and e["kind"] == "text" for e in brief.evidence))

    def test_source_is_never_executed(self):
        self.write("danger.py", "raise RuntimeError('upload module must not execute')\n")
        self.assertTrue(self.context.analyze("upload").evidence)

    def test_no_matches_no_invented_facts(self):
        brief = self.context.analyze("quuxquantum")
        self.assertEqual(brief.evidence, [])
        self.assertEqual(brief.observations, [])
        self.assertEqual(brief.questions, [])

    def test_input_validation_and_fts_escaping(self):
        for req in ["", "  ", None, "x" * 20001]:
            with self.assertRaises(ValueError):
                self.context.analyze(req)
        self.context.analyze('upload OR * " NEAR() --')
        with self.assertRaises(ValueError):
            self.context.analyze("upload", max_evidence=0)

    def test_excerpt_budget(self):
        self.write("long.md", "upload " * 2000)
        brief = self.context.analyze("upload", max_chars=200)
        self.assertLessEqual(sum(len(e["excerpt"]) for e in brief.evidence), 200)

    def test_valid_model_adapter(self):
        def model(payload):
            if payload["phase"] == "investigate":
                return {"actions": [], "done": True}
            return {"interpretations": [{"text": "Consider existing policy", "evidence_ids": [payload["evidence"][0]["id"]]}], "questions": []}
        self.context.model = model
        brief = self.context.analyze("upload")
        self.assertEqual(brief.mode, "model-investigation")
        self.assertEqual(len(brief.interpretations), 1)

    def test_hallucinated_model_citation_rejected(self):
        self.context.model = lambda p: {"actions": [], "done": True} if p["phase"] == "investigate" else {"interpretations": [{"text": "invented", "evidence_ids": ["E999"]}]}
        brief = self.context.analyze("upload")
        self.assertEqual(brief.interpretations, [])
        self.assertEqual(brief.mode, "retrieval-only")
        self.assertTrue(any("investigation failed" in w for w in brief.warnings))

    def test_model_exception_does_not_leak_secret(self):
        def model(payload):
            raise RuntimeError("secret-token-123")
        self.context.model = model
        brief = self.context.analyze("upload")
        self.assertNotIn("secret-token-123", brief.to_markdown())
        self.assertTrue(brief.evidence)

    def test_cache_root_binding(self):
        other = self.root / "other"
        other.mkdir()
        with self.assertRaises(ValueError):
            RequirementContext(other, cache=self.root / ".reqcontext/index.sqlite3")

    def test_gitignore(self):
        result = subprocess.run(["git", "init", "-q", str(self.root)], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.write(".gitignore", "ignored/\n")
        self.write("ignored/file.py", "def upload_private(): pass")
        brief = self.context.analyze("upload")
        self.assertFalse(any(e["path"].startswith("ignored/") for e in brief.evidence))

    def test_cli_json(self):
        result = subprocess.run([sys.executable, "-m", "reqcontext", str(self.root), "--requirement", "upload", "--format", "json", "--retrieval-only"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["requirement"], "upload")

    def test_persistence_after_reopen(self):
        self.context.remember(task="upload", question="Which?", answer="background")
        self.context.close()
        self.context = RequirementContext(self.root,refresh_mode="auto")
        self.assertEqual(len(self.context.analyze("upload").decisions), 1)

    def test_late_function_body_preserves_symbol(self):
        self.write("long_function.py", "def process_records():\n" + "    value = 1\n" * 80 + "    return unique_tail_marker()\n")
        evidence = self.context.analyze("unique_tail_marker").evidence
        hit = next(e for e in evidence if e["path"] == "long_function.py")
        self.assertEqual(hit["symbol"], "process_records")
        self.assertGreater(hit["start"], 60)

    def test_nested_calls_do_not_leak_to_parent(self):
        from reqcontext.index import chunks
        source = "def outer():\n    parent_call()\n    def inner():\n        child_call()\n    return inner\n"
        items = list(chunks("nested.py", source))
        outer = [i for i in items if i[3] == "outer"]
        inner = [i for i in items if i[3] == "outer.inner"]
        self.assertTrue(outer and inner)
        self.assertTrue(all("child_call" not in i[5] for i in outer))
        self.assertTrue(all("child_call" in i[5] for i in inner))

    def test_chunk_lines_are_nonoverlapping_and_complete(self):
        from reqcontext.index import chunks
        source = "# header\nclass Handler:\n    def upload(self):\n        return send()\n\n    def download(self):\n        return receive()\n"
        items = list(chunks("service.py", source))
        covered = [n for item in items for n in range(item[0], item[1] + 1)]
        self.assertEqual(covered, list(range(1, len(source.splitlines()) + 1)))
        self.assertIn("Handler.upload", [i[3] for i in items])

    def test_duplicate_symbol_windows_use_one_slot(self):
        self.write("long.py", "def unique_upload():\n" + "    upload()\n" * 90)
        evidence = self.context.analyze("unique_upload").evidence
        self.assertEqual(sum(e["symbol"] == "unique_upload" for e in evidence), 1)

    def test_schema_upgrade_preserves_decisions(self):
        self.context.remember(task="upload", question="Which?", answer="background", sources=["uploads.py"])
        self.context.index.db.execute("DELETE FROM metadata WHERE key='index_version'")
        self.context.index.db.commit()
        self.context.close()
        self.context = RequirementContext(self.root,refresh_mode="auto")
        brief = self.context.analyze("upload")
        self.assertEqual(len(brief.decisions), 1)
        self.assertEqual(brief.decisions[0]["status"], "user_confirmed")
        self.assertEqual(brief.index_stats["indexed"], 2)

    def test_test_request_can_retrieve_tests(self):
        self.write("tests/test_payment.py", "def test_payment_declined():\n    assert payment_declined()\n")
        self.write("payment.py", "def payment_declined():\n    return True\n")
        brief = self.context.analyze("test payment declined")
        self.assertTrue(any(e["path"] == "tests/test_payment.py" for e in brief.evidence))

    def test_definition_calls_not_in_class(self):
        from reqcontext.index import chunks
        items = list(chunks("x.py", "class Worker:\n    label = 'work'\n    def run(self):\n        execute()\n"))
        self.assertTrue(all("execute" not in i[5] for i in items if i[3] == "Worker"))


    def test_one_call_api(self):
        from reqcontext import analyze
        brief = analyze("upload", repo=self.root, retrieval_only=True)
        self.assertTrue(brief.evidence)

    def test_c_function_and_calls(self):
        from reqcontext import c_parser
        if not c_parser.available():
            self.skipTest("C extra not installed")
        self.write("upload.c", '/* fake() is a comment */\nstatic int upload_blob(int x) {\n    return send_blob(x);\n}\n')
        brief = self.context.analyze("upload_blob")
        hit = next(e for e in brief.evidence if e["path"] == "upload.c")
        self.assertEqual(hit["symbol"], "upload_blob")
        self.assertIn("send_blob", hit["calls"])
        self.assertNotIn("fake", hit["calls"])

    def test_c_pointer_return_multiline(self):
        from reqcontext import c_parser
        if not c_parser.available():
            self.skipTest("C extra not installed")
        items = c_parser.functions('static char *\nload_buffer(int n)\n{\n return alloc_buffer(n);\n}\n')
        self.assertEqual(items[0]["symbol"], "load_buffer")
        self.assertEqual(items[0]["calls"], {"alloc_buffer"})

    def test_c_text_fallback_without_extra(self):
        from unittest.mock import patch
        self.write("upload.c", 'int upload_blob(void) { return 0; }\n')
        with patch("reqcontext.c_parser.parser", return_value=None):
            brief = self.context.analyze("upload_blob")
        hit = next(e for e in brief.evidence if e["path"] == "upload.c")
        self.assertEqual(hit["symbol"], "")
        self.assertTrue(any("text only" in w for w in brief.warnings))

    def test_default_repo_and_stdin_cli(self):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
        result = subprocess.run([sys.executable, "-m", "reqcontext", "--requirement-file", "-", "--format", "json", "--retrieval-only"], cwd=self.root, env=environment, input="upload", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["evidence"])

    def test_parser_capability_change_reindexes(self):
        from reqcontext import c_parser
        from unittest.mock import patch
        if not c_parser.available():
            self.skipTest("C extra not installed")
        self.write("upload.c", 'int upload_blob(void) { return 0; }\n')
        with patch("reqcontext.c_parser.parser", return_value=None):
            with RequirementContext(self.root,refresh_mode="auto") as ctx:
                self.assertFalse(next(e for e in ctx.analyze("upload_blob").evidence if e["path"] == "upload.c")["symbol"])
        with RequirementContext(self.root,refresh_mode="auto") as ctx:
            brief = ctx.analyze("upload_blob")
            self.assertEqual(next(e for e in brief.evidence if e["path"] == "upload.c")["symbol"], "upload_blob")
            self.assertGreater(brief.index_stats["indexed"], 0)


    def test_macro_decorated_function_does_not_invent_void_symbol(self):
        from reqcontext import c_parser
        if not c_parser.available():
            self.skipTest("C extra not installed")
        items = c_parser.functions('static void __shr_constructor register_plugin(void) { register_extension(); }\n')
        self.assertFalse(any(item["symbol"] == "void" for item in items))



if __name__ == "__main__":
    unittest.main()
