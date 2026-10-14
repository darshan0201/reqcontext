"""Scripted adapters test mechanics only, not intelligent model quality."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reqcontext import RequirementContext, ChatModel, analyze


def report(evidence):
    policy = next(e for e in evidence if "Three attempts" in e["excerpt"])
    return {
        "interpretations": [{"text": "Use the applicable background-upload policy.", "evidence_ids": [policy["id"]]}],
        "constraints": [{"text": "Limit attempts to three.", "origin": "project_policy", "source_quote": "Three attempts", "evidence_ids": [policy["id"]], "applicability": "Background upload", "why_relevant": "Controls retry count"}],
        "questions": [], "unresolved": [],
    }


class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "service.py").write_text("def upload(data):\n    return remote_send(data)\n")
        (self.root / "policy.md").write_text("Three attempts for background uploads only.\n")

    def tearDown(self):
        self.temp.cleanup()

    def test_model_selects_search_read_then_reviews(self):
        phases = []
        def model(payload):
            phases.append(payload["phase"])
            if payload["phase"] == "investigate":
                if payload["round"] == 1:
                    return {"actions": [{"tool": "search", "query": "background uploads policy"}, {"tool": "list", "pattern": "*.md"}], "done": False}
                return {"actions": [{"tool": "read", "path": "policy.md", "start": 1, "end": 1}], "done": True}
            return report(payload["evidence"])
        with RequirementContext(self.root, model=model) as ctx:
            brief = ctx.analyze("Improve uploading")
        self.assertEqual(phases, ["investigate", "investigate", "finalize", "review"])
        self.assertEqual(brief.constraints[0]["origin"], "project_policy")
        self.assertEqual(brief.questions, [])
        self.assertEqual(brief.investigation["status"], "completed")

    def test_invalid_quote_rejected(self):
        def model(payload):
            if payload["phase"] == "investigate":
                return {"actions": [], "done": True}
            result = report(payload["evidence"])
            result["constraints"][0]["source_quote"] = "Unlimited attempts"
            return result
        with RequirementContext(self.root, model=model) as ctx:
            brief = ctx.analyze("background uploads policy")
        self.assertEqual(brief.constraints, [])
        self.assertEqual(brief.investigation["status"], "failed")

    def test_model_cannot_read_outside_index(self):
        phases = []
        def model(payload):
            if payload["phase"] == "investigate":
                return {"actions": [{"tool": "read", "path": "../../etc/passwd", "start": 1, "end": 80}], "done": True}
            phases.extend(payload["evidence"])
            return {"interpretations": [], "constraints": [], "questions": [], "unresolved": []}
        with RequirementContext(self.root, model=model) as ctx:
            brief = ctx.analyze("upload")
        self.assertEqual(brief.investigation["events"][0]["matching_chunks"], 0)
        self.assertTrue(all(e["path"] in {"service.py", "policy.md"} for e in phases))

    def test_adaptive_round_budget_terminates(self):
        calls = []
        def model(payload):
            calls.append(payload["phase"])
            if payload["phase"] == "investigate":
                return {"actions": [], "done": False}
            return {"interpretations": [], "constraints": [], "questions": [], "unresolved": ["Need further evidence"]}
        with RequirementContext(self.root, model=model) as ctx:
            brief = ctx.analyze("upload", max_rounds=2)
        self.assertEqual(len(calls), 4)
        self.assertEqual(brief.investigation["status"], "budget_exhausted")

    def test_question_needs_consequential_alternatives(self):
        def model(payload):
            if payload["phase"] == "investigate":
                return {"actions": [], "done": True}
            return {"questions": [{"question": "Retry?", "reason": "unclear", "evidence_ids": [], "alternatives": []}]}
        with RequirementContext(self.root, model=model) as ctx:
            brief = ctx.analyze("upload")
        self.assertEqual(brief.questions, [])
        self.assertEqual(brief.investigation["status"], "failed")

    def test_review_can_remove_unnecessary_question(self):
        def model(payload):
            if payload["phase"] == "investigate":
                return {"actions": [], "done": True}
            result = report(payload["evidence"])
            if payload["phase"] == "finalize":
                result["questions"] = [{"question": "How many attempts?", "reason": "candidate gap", "evidence_ids": [], "alternatives": [{"answer": "three", "effect": "three sends"}, {"answer": "five", "effect": "five sends"}]}]
            return result
        with RequirementContext(self.root, model=model) as ctx:
            brief = ctx.analyze("background uploads policy")
        self.assertEqual(brief.questions, [])

    def test_schema_limits_and_tool_rejection(self):
        with RequirementContext(self.root, model=lambda p: {"actions": [{"tool": "exec", "command": "rm"}], "done": True}) as ctx:
            brief = ctx.analyze("upload")
        self.assertEqual(brief.investigation["status"], "failed")

    def test_saved_clarifications_reach_model(self):
        observed = []
        def model(payload):
            observed.extend(payload["saved_clarifications"])
            if payload["phase"] == "investigate":
                return {"actions": [], "done": True}
            return {"interpretations": [], "constraints": [], "questions": [], "unresolved": []}
        with RequirementContext(self.root, model=model) as ctx:
            ctx.remember(task="upload", question="Scope?", answer="Background only")
            ctx.analyze("upload")
        self.assertEqual(observed[0]["answer"], "Background only")

    def test_one_call_requires_model_for_semantics(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "REQCONTEXT_BASE_URL"):
                analyze("upload", repo=self.root)

    def test_transport_role_separation_and_json(self):
        from unittest.mock import MagicMock
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({"choices": [{"message": {"content": '{"done":true,"actions":[]}'}}]}).encode()
        with patch("reqcontext.models.urlopen", return_value=response) as send:
            model = ChatModel(base_url="http://localhost:8000/v1", model="local-model")
            self.assertTrue(model({"instruction": "trusted", "requirement": "untrusted"})["done"])
        request = send.call_args.args[0]
        data = json.loads(request.data)
        self.assertEqual(data["messages"][0]["role"], "system")
        self.assertEqual(data["messages"][0]["content"], "trusted")
        self.assertEqual(json.loads(data["messages"][1]["content"])["requirement"], "untrusted")

    def test_symbol_read_does_not_pull_neighbor_function(self):
        (self.root / "service.py").write_text("def upload(data):\n    return remote_send(data)\n\ndef unrelated():\n    return neighboring_only()\n")
        from reqcontext.investigation import Investigator
        with RequirementContext(self.root) as ctx:
            brief = ctx.analyze("no_matching_term")
            investigator = Investigator(ctx, brief)
            event = investigator.execute({"tool": "read_symbol", "path": "service.py", "symbol": "upload"})
        self.assertGreater(event["matching_chunks"], 0)
        self.assertTrue(event["new_evidence_ids"])
        self.assertTrue(all("neighboring_only" not in e["excerpt"] for e in brief.evidence))

    def test_symbol_read_respects_evidence_budget(self):
        from reqcontext.investigation import Investigator
        (self.root / "big.py").write_text("def upload(data):\n" + "    value = data\n" * 100)
        with RequirementContext(self.root) as ctx:
            brief = ctx.analyze("no_matching_term")
            investigator = Investigator(ctx, brief, max_chars=200)
            investigator.execute({"tool": "read_symbol", "path": "big.py", "symbol": "upload"})
        self.assertLessEqual(sum(len(e["excerpt"]) for e in brief.evidence), 200)
