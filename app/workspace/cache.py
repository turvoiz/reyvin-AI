from app.workspace.call_graph import call_graph
from app.workspace.impact import impact_analyzer
from app.workspace.deadcode import deadcode_analyzer
from app.workspace.graph import dependency_graph
from app.workspace.references import reference_index
from app.workspace.resolver import resolver_index
from app.workspace.symbols import build_symbol_index
from app.workspace.tracer import trace_engine
from app.workspace.knowledge import knowledge_builder
from app.workspace.context_builder import context_builder
from app.workspace.storage.snapshot import workspace_snapshot
from app.workspace.index.file_state import file_state
from app.workspace.rebuilder.incremental import incremental_rebuilder


class WorkspaceCache:

    def __init__(self):

        self.workspace = "."

        self._symbols = {}

        self._graph = {}

        self._references = {}

        self._resolver = {}

        self._calls = {}

        self._trace = {}
        self._knowledge = {}

        self._files = {}

        self._files = {}

    def load(self, workspace="."):

        self.workspace = workspace

        self._knowledge.clear()

        snapshot = workspace_snapshot.load()

        if snapshot:

            print("[Workspace] Loaded snapshot")

            self.import_data(snapshot)

            return

        print("[Workspace] Building workspace...")

        self._symbols = build_symbol_index(workspace)

        self._graph = dependency_graph.build(workspace)

        self._references = reference_index.build(workspace)

        self._resolver = resolver_index.build(workspace)

        self._calls = call_graph.build(workspace)

        self._trace = trace_engine

        self._files = file_state.scan(workspace)

        workspace_snapshot.save(
            self.export()
        )



    def rebuild(self):

        result = self.accept_changes()

        return incremental_rebuilder.rebuild(
            self,
            result["changed"],
        )

    def reload(self):

        self.load(self.workspace)

    def symbols(self):
        return self._symbols

    def graph(self):
        return self._graph

    def references(self):
        return self._references

    def resolver(self):
        return self._resolver

    def calls(self, symbol=None):

        if symbol is None:
            return self._calls["forward"]

        return self._calls["forward"].get(symbol, [])

    def callers(self, symbol):

        return self._calls["reverse"].get(symbol, [])


    def impact(self, symbol):

        affected = impact_analyzer.analyze(
            self._calls["reverse"],
            symbol,
        )

        files = set()

        for target in affected:

            info = self._symbols.get(target)

            if info:
                files.add(info["file"])

        risk = "none"

        if len(affected) >= 5:
            risk = "high"
        elif len(affected) >= 2:
            risk = "medium"
        elif affected:
            risk = "low"

        return {
            "symbol": symbol,
            "affected_symbols": affected,
            "affected_files": sorted(files),
            "risk": risk,
        }

    def trace(self, symbol):
        return self._trace.trace(
            self._calls["forward"],
            symbol,
        )



    def deadcode(self):

        return deadcode_analyzer.analyze(
            self._symbols,
            self._calls["reverse"],
        )




    def context(self, symbol):

        info = self.get(symbol)

        if not info:
            return ""

        return context_builder.build(info)


    def knowledge(self, symbol):

        if symbol in self._knowledge:
            return self._knowledge[symbol]

        knowledge = knowledge_builder.build(
            self,
            symbol,
        )

        self._knowledge[symbol] = knowledge

        return knowledge





    def import_data(self, data):

        self._symbols = data["symbols"]
        self._graph = data["graph"]
        self._references = data["references"]
        self._resolver = data["resolver"]
        self._calls = data["calls"]
        self._files = data.get("files", {})

        self._trace = trace_engine


    def export(self):

        return {
            "symbols": self._symbols,
            "graph": self._graph,
            "references": self._references,
            "resolver": self._resolver,
            "calls": self._calls,
            "files": self._files,
        }






    def accept_changes(self):

        result = file_state.changed(
            self._files,
            self.workspace,
        )

        self._files = result["state"]

        workspace_snapshot.save(
            self.export()
        )

        return result


    def changed_files(self):

        return file_state.changed(
            self._files,
            self.workspace,
        )


    def invalidate(
        self,
        symbols,
    ):

        for symbol in symbols:
            self._knowledge.pop(symbol, None)


    def stats(self):

        return {
            "symbols": len(self._symbols),
            "knowledge_cache": len(self._knowledge),
        }


    def get(self, name):
        return self._symbols.get(name)


workspace_cache = WorkspaceCache()