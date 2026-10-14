import unittest
from reqcontext.core import Brief


class MarkdownTests(unittest.TestCase):
    def test_optional_fingerprints_do_not_change_json_provenance(self):
        digest = "a" * 64
        evidence = [dict(id=f"E{i}", path="service.py", start=i, end=i,
                         symbol="send", kind="function", hash=digest)
                    for i in (1, 2)]
        brief = Brief("Add retries", evidence, [], [], [], [], {})
        original = brief.to_dict()
        readable = brief.to_markdown()
        self.assertIn("service.py:1-1", readable)
        self.assertIn("service.py:2-2", readable)
        self.assertNotIn(digest, readable)
        detailed = brief.to_markdown(include_provenance=True)
        self.assertEqual(detailed.count(digest), 1)
        self.assertEqual(brief.to_dict(), original)


if __name__ == "__main__":
    unittest.main()
