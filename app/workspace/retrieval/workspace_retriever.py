class WorkspaceRetriever:
    def retrieve(
        self,
        cache,
        symbol,
    ):

        knowledge = cache.knowledge(symbol)

        return {
            "symbol": knowledge.get("symbol"),
            "source": knowledge.get("source"),
            "calls": knowledge.get("calls", []),
            "callers": knowledge.get("callers", []),
            "references": knowledge.get("references", []),
            "dependencies": knowledge.get("dependencies", []),
            "impact": knowledge.get("impact"),
            "trace": knowledge.get("trace"),
            "imports": cache.graph().get("imports", {}),
            "reverse_imports": cache.graph().get("reverse", {}),
        }


workspace_retriever = WorkspaceRetriever()
