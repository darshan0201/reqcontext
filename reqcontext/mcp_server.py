"""MCP stdio adapter: host-model investigation using stored source snapshots."""
import argparse
from .core import RequirementContext, Brief
from .investigation import Investigator
from .models import ChatModel

class SnapshotTools:
    def __init__(self, repo, snapshot=None, documents=()):
        self.repo,self.snapshot,self.documents=repo,snapshot,documents
    def overview(self):
        with RequirementContext(self.repo,cache=self.snapshot,documents=self.documents) as ctx:
            stats=ctx.index.ensure_snapshot()
            return {"snapshot":ctx.index.snapshot(),"folders":ctx.index.folder_map(),"stats":stats,"warning":"Stored snapshot; no live freshness scan. Refresh explicitly after changes."}
    def lookup(self, action):
        with RequirementContext(self.repo,cache=self.snapshot,documents=self.documents) as ctx:
            stats=ctx.index.ensure_snapshot()
            brief=Brief("Snapshot lookup",[],[],[],[],[],stats)
            brief.snapshot=ctx.index.snapshot()
            result=Investigator(ctx,brief,max_chars=20000).execute(action)
            return {"result":result,"evidence":brief.evidence,"snapshot":brief.snapshot,"citation_note":"Evidence IDs are local to this response; cite source path/page/hash across calls."}
    def refresh(self):
        with RequirementContext(self.repo,cache=self.snapshot,documents=self.documents) as ctx:
            stats=ctx.refresh()
            return {"snapshot":ctx.index.snapshot(),"stats":stats}
    def analyze(self, requirement):
        with RequirementContext(self.repo,cache=self.snapshot,documents=self.documents,model=ChatModel.from_env()) as ctx:
            return ctx.analyze(requirement).to_dict()

def create_server(tools):
    from mcp.server.fastmcp import FastMCP
    server=FastMCP("ReqContext",instructions="Start with project_orientation, then describe_component to select relevant folders. Use related_components to inspect evidence-backed dependencies and consumers when needed. These map tools require a prebuilt map and never scan source. Use the separate source-snapshot tools only for deeper investigation; their first use may build a missing snapshot. Explain folder selection with source citations. Existing code is not automatically normative. Normal lookup does not scan live files. Refresh explicitly when a new snapshot is needed.")
    @server.tool()
    def project_orientation() -> str:
        """Load the saved project map at session start, without scanning source files. Build it first with reqcontext map build DIRECTORY."""
        from .project_map import ProjectMap
        return ProjectMap(tools.repo).overview()

    @server.tool()
    def describe_component(folder: str = ".") -> dict:
        """Expand a folder from the saved project orientation map."""
        from .project_map import ProjectMap
        return ProjectMap(tools.repo).describe(folder)

    @server.tool()
    def related_components(folder: str = ".") -> dict:
        """Expand one component to dependencies and consumers with saved import evidence. Full map required for relationships; other-language/dynamic links remain unknown."""
        from .project_map import ProjectMap
        return ProjectMap(tools.repo).related(folder)

    @server.tool()
    def repository_overview() -> dict:
        """Read snapshot capture information and root folder counts."""
        return tools.overview()
    @server.tool()
    def snapshot_lookup(action: dict) -> dict:
        """Actions: folders(prefix), symbols(query,prefix optional), search(query,prefix optional), read_symbol(path,symbol), read(path,start,end <=120 lines), neighbors(path,symbol), read_document(path,page). Read indexed sources only."""
        return tools.lookup(action)
    @server.tool()
    def refresh_repository_snapshot() -> dict:
        """Explicitly rescan live files and update snapshot. Normal lookup never scans."""
        return tools.refresh()
    @server.tool()
    def analyze_requirement(requirement: str) -> dict:
        """Optional nested-model analysis using REQCONTEXT endpoint settings. Host can instead reason directly through overview/lookup with no separate model endpoint."""
        return tools.analyze(requirement)
    return server

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo',required=True)
    p.add_argument('--snapshot')
    p.add_argument('--document',action='append',default=[])
    a=p.parse_args()
    create_server(SnapshotTools(a.repo,a.snapshot,a.document)).run(transport='stdio')
if __name__=='__main__':
    main()
