"""Non-storage repository snapshot evaluation; no autonomous model claims."""
import argparse,json,statistics,subprocess,tempfile,time
from pathlib import Path
from unittest.mock import patch
from reqcontext import RequirementContext
from reqcontext.investigation import Investigator

CASES=[
 ('Stop forwarding authorization credentials when redirecting to another origin.','httpx/_client.py','BaseClient._redirect_headers'),
 ('Ignore environment proxy settings when trust_env is disabled.','httpx/_client.py','BaseClient._get_proxy_map'),
 ('Configure different timeout values for connect, read, write and pool acquisition.','httpx/_config.py','Timeout'),
 ('Stream response bytes in configurable chunk sizes.','httpx/_models.py','Response.iter_bytes'),
 ('Set limits on total connections and keep-alive connections.','httpx/_config.py','Limits'),
 ('Merge client cookies with cookies supplied for an individual request.','httpx/_client.py','BaseClient._merge_cookies'),
]

def main():
 p=argparse.ArgumentParser();p.add_argument('repo',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 with tempfile.TemporaryDirectory() as d,RequirementContext(a.repo,cache=Path(d)/'snapshot.db') as ctx:
  t=time.perf_counter();ctx.refresh();build=time.perf_counter()-t
  results=[]
  with patch('reqcontext.index.Index.paths',side_effect=AssertionError('unexpected scan')):
   for req,path,symbol in CASES:
    t=time.perf_counter();brief=ctx.analyze(req,max_evidence=5);elapsed=time.perf_counter()-t
    scoped=ctx.index.search(req,limit=5,prefix='httpx')
    finder=Investigator(ctx,brief,max_chars=20000)
    event=finder.execute({'tool':'read_symbol','path':path,'symbol':symbol})
    results.append({'requirement':req,'expected_primary_path':path,'expected_symbol_or_family':symbol,
     'whole_snapshot_file_rank':next((i for i,e in enumerate(brief.evidence[:5],1) if e['path']==path),None),
     'whole_snapshot_symbol_rank':next((i for i,e in enumerate(brief.evidence[:5],1) if e['path']==path and (e['symbol']==symbol or e['symbol'].startswith(symbol+'.'))),None),
     'httpx_scoped_file_rank':next((i for i,e in enumerate(scoped,1) if e['path']==path),None),
     'snapshot_query_seconds':elapsed,'source_files_read':brief.index_stats['source_files_read'],
     'symbol_lookup_succeeded':event['matching_chunks']>0,
     'initial_results':[{'path':e['path'],'symbol':e['symbol']} for e in brief.evidence[:5]]})
  report={'repo':'https://github.com/encode/httpx','commit':subprocess.run(['git','-C',str(a.repo),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip(),
   'method':'Six manually authored requirements, inspected primary symbol locations. Arbitrary non-storage repo selection, not statistically random sampling. No model calls. Exact-symbol lookup uses known expected targets and is not a discovery metric.',
   'snapshot':ctx.index.snapshot(),'build_seconds':build,'query_median_seconds':statistics.median(r['snapshot_query_seconds'] for r in results),
   'file_hits_at_5':sum(r['whole_snapshot_file_rank'] is not None for r in results),'symbol_hits_at_5':sum(r['whole_snapshot_symbol_rank'] is not None for r in results),
   'folder_scoped_file_hits_at_5':sum(r['httpx_scoped_file_rank'] is not None for r in results),'all_snapshot_queries_blocked_live_enumeration':True,'results':results}
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in {'results','method','snapshot'}},indent=2))
if __name__=='__main__':main()
