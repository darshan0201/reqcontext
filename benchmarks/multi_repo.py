"""Read-only retrieval evaluation. Targets reviewed in public source.

Usage: PYTHONPATH=. python benchmarks/multi_repo.py --repos ../repo-eval --output benchmarks/baseline.json
Keep fixed queries when comparing versions. Pass --profile to save cold-index profile.
"""
import argparse
import cProfile
import json
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile
import time
from reqcontext import RequirementContext

CASES = {
    "click": [
        ("tune", "Allow the confirmation prompt to accept a custom default answer", "src/click/termui.py", "confirm"),
        ("tune", "Make choice parameter validation ignore case", "src/click/types.py", "Choice"),
        ("holdout", "Change how a command group resolves an unknown subcommand", "src/click/core.py", "Group.resolve_command"),
        ("holdout", "Support entering a hidden password twice for confirmation", "src/click/termui.py", "prompt"),
    ],
    "requests": [
        ("tune", "Limit redirects and preserve request history", "src/requests/sessions.py", "SessionRedirectMixin.resolve_redirects"),
        ("tune", "Configure automatic retries for failed HTTP connections", "src/requests/adapters.py", "HTTPAdapter"),
        ("holdout", "Respect proxy environment variables when preparing session settings", "src/requests/sessions.py", "Session.merge_environment_settings"),
        ("holdout", "Customize how a request body is prepared from JSON data", "src/requests/models.py", "PreparedRequest.prepare_body"),
    ],
    "jinja": [
        ("tune", "Reload a cached template when its source file changes", "src/jinja2/environment.py", "Environment._load_template"),
        ("tune", "Search multiple filesystem directories for a template", "src/jinja2/loaders.py", "FileSystemLoader"),
        ("holdout", "Change parsing of the for loop and its optional else block", "src/jinja2/parser.py", "Parser.parse_for"),
        ("holdout", "Choose HTML autoescaping based on a template filename extension", "src/jinja2/utils.py", "select_autoescape"),
    ],
}


def command(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repos", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--profile", action="store_true")
    p.add_argument("--split", choices=["all", "tune", "holdout"], default="all")
    args = p.parse_args()
    report = {"python": platform.python_version(), "repositories": {}, "method": "Four manually authored queries per repository; 2 tuning + 2 held-out. File hit@5 and symbol hit@5, not end-to-end agent correctness. Same machine; caches and timing vary."}
    for name, cases in CASES.items():
        root = (args.repos / name).resolve()
        with tempfile.TemporaryDirectory() as directory:
            with RequirementContext(root, cache=Path(directory) / "index.db") as ctx:
                profiler = cProfile.Profile()
                start = time.perf_counter()
                if args.profile:
                    profiler.enable()
                stats = ctx.index.refresh()
                if args.profile:
                    profiler.disable()
                    profiler.dump_stats(str(args.output.with_suffix(f".{name}.prof")))
                cold = time.perf_counter() - start
                timings = []
                for _ in range(5):
                    start = time.perf_counter()
                    warm = ctx.index.refresh()
                    timings.append(time.perf_counter() - start)
                queries = []
                for split, query, path, symbol in cases:
                    if args.split != "all" and split != args.split:
                        continue
                    start = time.perf_counter()
                    brief = ctx.analyze(query, max_evidence=5)
                    elapsed = time.perf_counter() - start
                    rank = next((i for i, e in enumerate(brief.evidence, 1) if e["path"] == path), None)
                    symbol_rank = next((i for i, e in enumerate(brief.evidence, 1) if e["path"] == path and (e["symbol"] == symbol or e["symbol"].startswith(symbol + "."))), None)
                    queries.append({"split": split, "query": query, "expected_path": path, "expected_symbol": symbol,
                                    "file_rank": rank, "symbol_rank": symbol_rank, "seconds": elapsed,
                                    "results": [{"path": e["path"], "symbol": e["symbol"], "score": round(e["score"], 4)} for e in brief.evidence],
                                    "questions": len(brief.questions)})
                report["repositories"][name] = {"url": command(root, "remote", "get-url", "origin"), "commit": command(root, "rev-parse", "HEAD"), "cold_seconds": cold, "warm_median_seconds": statistics.median(timings), "cold_stats": stats, "warm_stats": warm, "chunks": ctx.index.db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0], "cache_bytes": (Path(directory) / "index.db").stat().st_size, "queries": queries}
    queries = [q for r in report["repositories"].values() for q in r["queries"]]
    report["summary"] = {s: {"count": len(sub := [q for q in queries if s == "all" or q["split"] == s]), "file_hits_at_5": sum(q["file_rank"] is not None for q in sub), "symbol_hits_at_5": sum(q["symbol_rank"] is not None for q in sub)} for s in ["all", "tune", "holdout"]}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"summary": report["summary"], "timing": {k: {x: v[x] for x in ["cold_seconds", "warm_median_seconds", "cache_bytes"]} for k, v in report["repositories"].items()}}, indent=2))

if __name__ == "__main__":
    main()
