import argparse
import json
import sys
from pathlib import Path
from .core import RequirementContext


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ground requirements in a local repository. No API key required.")
    parser.add_argument("repo", help="Repository directory")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--requirement", help="Requirement text")
    group.add_argument("--requirement-file", type=Path)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--exclude", action="append", default=[], help="Additional relative-path glob; repeatable")
    parser.add_argument("--max-evidence", type=int, default=8)
    args = parser.parse_args(argv)
    try:
        requirement = args.requirement if args.requirement is not None else args.requirement_file.read_text(encoding="utf-8")
        with RequirementContext(args.repo, excludes=args.exclude) as context:
            brief = context.analyze(requirement, max_evidence=args.max_evidence)
        print(json.dumps(brief.to_dict(), indent=2) if args.format == "json" else brief.to_markdown(), end="\n")
        return 0
    except (ValueError, OSError) as error:
        print(f"reqcontext: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
