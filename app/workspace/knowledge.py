class KnowledgeBuilder:
    def build(
        self,
        cache,
        symbol,
    ):

        info = cache.get(symbol)

        if not info:
            return None

        return {
            "source": cache.context(symbol),
            "symbol": info,
            "calls": cache.calls(symbol),
            "callers": cache.callers(symbol),
            "impact": cache.impact(symbol),
            "references": cache.references().get(symbol, []),
            "dependencies": cache.graph()["imports"].get(
                info["file"],
                [],
            ),
            "trace": cache.trace(symbol),
        }


knowledge_builder = KnowledgeBuilder()
