"""Read-only NVMe smoke evaluation. No commands are sent to an NVMe device."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time
from reqcontext import RequirementContext

QUERIES = [
    "Report reservation registrants in JSON format",
    "Download firmware image in chunks with an offset",
    "Show the sanitize status progress log",
    "Read the error log with a configurable number of entries",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp, RequirementContext(args.repo, cache=Path(temp)/"index.db") as context:
        results = []
        for query in QUERIES:
            start = time.perf_counter()
            brief = context.analyze(query, max_evidence=5)
            results.append({"query": query, "seconds": time.perf_counter()-start,
                            "stats": brief.index_stats,
                            "results": [{"path": e["path"], "symbol": e["symbol"]} for e in brief.evidence]})
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
