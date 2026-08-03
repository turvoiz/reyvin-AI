from app.workspace.scanner import scan_workspace
from app.workspace.symbols import build_symbol_index


class WorkspaceIndexer:
    def index(self, workspace: str):

        files = scan_workspace(workspace)

        symbols = build_symbol_index(workspace)

        return {
            "total_files": len(files),
            "files": files,
            "total_symbols": len(symbols),
            "symbols": symbols,
        }


indexer = WorkspaceIndexer()
