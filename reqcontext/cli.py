import argparse
import json
import sys
from pathlib import Path
from .core import RequirementContext
from .models import ChatModel


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "map":
        return map_cli(argv[1:])
    if argv and argv[0] == "snapshot":
        return snapshot_cli(argv[1:])
    parser = argparse.ArgumentParser(description="Ground requirements in a local repository. Model endpoint configured through REQCONTEXT environment settings.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository directory (default: current directory)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--requirement", help="Requirement text")
    group.add_argument("--requirement-file", type=Path, help="Text file, or - to read standard input")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--exclude", action="append", default=[], help="Additional relative-path glob; repeatable")
    parser.add_argument("--max-evidence", type=int, default=8)
    parser.add_argument("--retrieval-only", action="store_true", help="Return indexed evidence without model interpretation")
    parser.add_argument("--max-rounds", type=int, default=4, help="Maximum model-selected investigation rounds")
    parser.add_argument("--snapshot", help="Snapshot SQLite path; defaults to repo/.reqcontext/index.sqlite3")
    parser.add_argument("--refresh", action="store_true", help="Refresh source snapshot before analyzing")
    parser.add_argument("--document", action="append", default=[], help="Local PDF/text reference; repeatable")
    args = parser.parse_args(argv)
    try:
        requirement = args.requirement if args.requirement is not None else (sys.stdin.read() if str(args.requirement_file) == "-" else args.requirement_file.read_text(encoding="utf-8"))
        model = None if args.retrieval_only else ChatModel.from_env()
        with RequirementContext(args.repo, excludes=args.exclude, model=model,cache=args.snapshot,documents=args.document) as context:
            if args.refresh:
                context.refresh()
            brief = context.analyze(requirement, max_evidence=args.max_evidence, max_rounds=args.max_rounds)
        print(json.dumps(brief.to_dict(), indent=2) if args.format == "json" else brief.to_markdown(), end="\n")
        return 3 if brief.investigation.get("status") == "failed" else 0
    except (ValueError, OSError) as error:
        print(f"reqcontext: {error}", file=sys.stderr)
        return 2


def snapshot_cli(argv):
    parser = argparse.ArgumentParser(description="Build or explicitly refresh a repository snapshot")
    parser.add_argument("operation",choices=["build","refresh"])
    parser.add_argument("repo")
    parser.add_argument("--output",required=True)
    parser.add_argument("--document",action="append",default=[])
    args=parser.parse_args(argv)
    try:
        with RequirementContext(args.repo,cache=args.output,documents=args.document) as context:
            stats=context.refresh()
            print(json.dumps({"snapshot":context.index.snapshot(),"stats":stats},indent=2))
        return 0
    except (ValueError,OSError) as error:
        print(f"reqcontext: {error}",file=sys.stderr)
        return 2


def map_cli(argv):
    from .project_map import ProjectMap
    parser = argparse.ArgumentParser(description="Persistent project orientation for fresh sessions")
    parser.add_argument("operation", choices=["build", "refresh", "session", "describe"])
    parser.add_argument("directory")
    parser.add_argument("--cache", help="Optional map path outside the project")
    parser.add_argument("--folder", default=".")
    parser.add_argument("--with-model", action="store_true", help="Send bounded samples to the configured model for folder descriptions")
    args = parser.parse_args(argv)
    try:
        project = ProjectMap(args.directory, cache=args.cache)
        if args.operation in {"build", "refresh"}:
            result = project.build(refresh=args.operation == "refresh", model=ChatModel.from_env() if args.with_model else None)
            print(json.dumps({"cache": str(project.cache), "folders": len(result["map"]["folders"]), "reused": result["reused"], "source_files_read": result["source_files_read"]}, indent=2))
        elif args.operation == "session":
            print(project.overview())
        else:
            print(json.dumps(project.describe(args.folder), indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(f"reqcontext: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
