"""Actual stdio initialize/list/call test against the optional MCP SDK."""
import asyncio,json,os,sys,tempfile
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)/'repo';root.mkdir();(root/'src').mkdir()
        (root/'src/service.py').write_text('def submit_upload(data):\n    return data\n')
        env=dict(os.environ);env['PYTHONPATH']=str(Path(__file__).resolve().parents[1])
        parameters=StdioServerParameters(command=sys.executable,args=['-m','reqcontext.mcp_server','--repo',str(root),'--snapshot',str(Path(temp)/'snapshot.db')],env=env)
        async with stdio_client(parameters) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                available=await session.list_tools()
                names=[t.name for t in available.tools]
                assert 'repository_overview' in names and 'snapshot_lookup' in names
                overview=await session.call_tool('repository_overview',{})
                result=await session.call_tool('snapshot_lookup',{'action':{'tool':'read_symbol','path':'src/service.py','symbol':'submit_upload'}})
                assert not result.isError
                raw=result.structuredContent
                if raw is None:
                    raw=json.loads(next(c.text for c in result.content if hasattr(c,'text')))
                assert raw['evidence'][0]['symbol']=='submit_upload'
                print(json.dumps({'transport':'stdio','tools':names,'initialize_list_call_passed':True,'selected_symbol':'submit_upload'},indent=2))

if __name__=='__main__':asyncio.run(run())
