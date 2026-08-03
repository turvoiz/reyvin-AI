from app.workspace.retrieval.symbol_expander import symbol_expander
from app.workspace.ranking.context_ranker import context_ranker


class WorkspaceRetriever:

    def retrieve(
        self,
        cache,
        symbol,
    ):

        knowledge = cache.knowledge(symbol)

        related = symbol_expander.expand(
            cache,
            symbol,
        )

        knowledge_calls = [
            item["call"]
            for item in knowledge.get("calls", [])
        ]

        knowledge_callers = [
            item["caller"]
            for item in knowledge.get("callers", [])
        ]

        priority = (
            knowledge_calls
            + knowledge_callers
            + related
        )

        related = context_ranker.rank(
            symbol,
            cache,
            priority,
        )

        related_sources = []
        seen = set()

        for related_symbol in related:

            if related_symbol == symbol:
                continue

            info = cache.get(related_symbol)

            if not info:
                continue

            source = cache.context(related_symbol)

            if not source:
                continue

            if related_symbol in seen:
                continue

            seen.add(related_symbol)

            related_sources.append({
                "symbol": related_symbol,
                "type": info["type"],
                "source": source,
            })

        return {
            "symbol": knowledge.get("symbol"),
            "source": knowledge.get("source"),
            "calls": knowledge.get("calls", []),
            "callers": knowledge.get("callers", []),
            "references": knowledge.get("references", []),
            "dependencies": knowledge.get("dependencies", []),
            "impact": knowledge.get("impact"),
            "trace": knowledge.get("trace"),
            "related_sources": related_sources,
            "imports": cache.graph().get("imports", {}),
            "reverse_imports": cache.graph().get("reverse", {}),
        }


workspace_retriever = WorkspaceRetriever()
