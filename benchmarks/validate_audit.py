"""Validate saved audit reports against their actual captured evidence snapshots.

This replays validation, not fresh model inference. It never executes NVMe commands.
"""
import json
from pathlib import Path
from reqcontext.investigation import validate_final

root = Path(__file__).parent / "agent-audit"
for case in ["fw-retry", "reservation"]:
    folder=root/case
    request=json.loads((folder/"request-5.json").read_text())
    response=json.loads((folder/"response-5.json").read_text())
    checked=validate_final(response,request["evidence"],request["requirement"])
    print(case, len(checked["constraints"]), "constraints", len(checked["questions"]), "questions: valid citations and quotations")
