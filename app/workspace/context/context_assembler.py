from app.workspace.ranking.workspace_ranker import workspace_ranker
from app.workspace.retrieval.workspace_retriever import workspace_retriever


class ContextAssembler:
    def build(
        self,
        cache,
        symbol,
        intent="explain",
    ):

        context = workspace_retriever.retrieve(
            cache,
            symbol,
        )

        context["top_symbols"] = workspace_ranker.top(
            context,
        )

        context["intent"] = intent

        if intent == "review":
            context["related_sources"] = [
                x for x in context.get("related_sources", [])
                if x["symbol"] in [
                    c["caller"]
                    for c in context.get("callers", [])
                ]
            ]

        elif intent == "impact":
            context["related_sources"] = [
                x for x in context.get("related_sources", [])
                if x["symbol"] in [
                    i
                    for i in context.get("impact", {}).get(
                        "affected_symbols",
                        []
                    )
                ]
            ]

        return context


context_assembler = ContextAssembler()
