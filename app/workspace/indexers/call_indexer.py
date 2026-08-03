from app.workspace.call_graph import call_graph


class CallIndexer:
    def build(self, workspace):

        return call_graph.build(workspace)

    def update(
        self,
        cache,
        workspace,
    ):

        cache._calls = call_graph.build(
            workspace,
            symbols=cache._symbols,
            resolver=cache._resolver,
        )


call_indexer = CallIndexer()
