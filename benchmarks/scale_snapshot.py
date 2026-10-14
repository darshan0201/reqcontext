"""Synthetic scale test: indexing versus stored-snapshot queries. No model calls."""
import argparse,json,statistics,tempfile,time,resource
from pathlib import Path
from reqcontext import RequirementContext

def measure(count):
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)/'repo';root.mkdir()
        for i in range(count):
            folder=root/'src'/f'feature_{i%100:03d}';folder.mkdir(parents=True,exist_ok=True)
            text='\n'.join(f'def process_{j}(value):\n    return transform(value)\n' for j in range(6))
            if i==0:text+='\ndef submit_upload(image):\n    return transfer_image(image)\n'
            (folder/f'module_{i:05d}.py').write_text(text)
        cache=Path(temp)/'snapshot.db'
        with RequirementContext(root,cache=cache) as ctx:
            t=time.perf_counter();first=ctx.analyze('submit upload image');cold=time.perf_counter()-t
            times=[]
            for _ in range(9):
                t=time.perf_counter();brief=ctx.analyze('submit upload image');times.append(time.perf_counter()-t)
                assert brief.index_stats['source_files_read']==0
            target=next((e for e in brief.evidence if e['symbol']=='submit_upload'),None)
            assert target
            t=time.perf_counter();hits=ctx.index.search('submit upload image',prefix='src/feature_000');scoped=time.perf_counter()-t
            return {'files':count,'functions':count*6+1,'cold_build_and_query_seconds':cold,
                    'snapshot_analysis_median_seconds':statistics.median(times),'scoped_search_seconds':scoped,
                    'source_files_read_per_snapshot_analysis':0,'snapshot_bytes':cache.stat().st_size,
                    'process_peak_rss_mb_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                    'target_found':True,'snapshot':ctx.index.snapshot()}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report={'method':'Synthetic Python files, standard local storage, nine repeated snapshot analyses. Peak RSS is cumulative process high-water mark. No model reasoning or token/quality measurement.','results':[measure(n) for n in [1000,10000]]}
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
