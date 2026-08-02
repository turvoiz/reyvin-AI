from app.workspace.ranking.workspace_ranker import workspace_ranker
from app.workspace.retrieval.workspace_retriever import workspace_retriever


class ContextAssembler:
    def build(
        self,
        cache,
        symbol,
    ):

        context = workspace_retriever.retrieve(
            cache,
            symbol,
        )

        context["top_symbols"] = workspace_ranker.top(
            context,
        )

        return context


context_assembler = ContextAssembler()
