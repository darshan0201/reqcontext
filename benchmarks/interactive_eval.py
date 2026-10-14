"""Manually facilitated model-interface audit; no autonomous endpoint claim.

Run repeatedly: each run replays recorded responses, executes the library's tool
loop, then writes the next missing request. Supply its response and run again.
This avoids holding a SQLite connection open between orchestration tool calls.
"""
import argparse
import json
from pathlib import Path
from reqcontext import RequirementContext

class PendingModel(BaseException):
    pass


def main():
    p=argparse.ArgumentParser()
    p.add_argument('repo', type=Path)
    p.add_argument('exchange', type=Path)
    p.add_argument('--requirement', required=True)
    args=p.parse_args()
    args.exchange.mkdir(parents=True, exist_ok=True)
    counter=0
    def model(payload):
        nonlocal counter
        counter+=1
        request=args.exchange/f'request-{counter}.json'
        response=args.exchange/f'response-{counter}.json'
        request.write_text(json.dumps(payload, indent=2))
        if not response.exists():
            print(f'Pending {response.name}: {payload["phase"]}')
            raise PendingModel()
        return json.loads(response.read_text())
    try:
        with RequirementContext(args.repo,cache=args.exchange/'index.db',model=model) as ctx:
            brief=ctx.analyze(args.requirement,max_evidence=5,max_chars=30000,max_rounds=4)
    except PendingModel:
        return
    (args.exchange/'brief.json').write_text(json.dumps(brief.to_dict(),indent=2))
    (args.exchange/'brief.md').write_text(brief.to_markdown())
    print(brief.investigation['status'])

if __name__=='__main__':
    main()
