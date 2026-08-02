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


class WorkspaceCache:

    def __init__(self):

        self.workspace = "."

        self._symbols = {}

        self._graph = {}

        self._references = {}

        self._resolver = {}

        self._calls = {}

        self._trace = {}

    def load(self, workspace="."):

        self.workspace = workspace

        self._symbols = build_symbol_index(workspace)

        self._graph = dependency_graph.build(workspace)

        self._references = reference_index.build(workspace)

        self._resolver = resolver_index.build(workspace)

        self._calls = call_graph.build(workspace)

        self._trace = trace_engine

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

        return knowledge_builder.build(
            self,
            symbol,
        )


    def get(self, name):
        return self._symbols.get(name)


workspace_cache = WorkspaceCache()