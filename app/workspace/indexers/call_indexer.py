from app.workspace.call_graph import call_graph


class CallIndexer:

    def build(self, workspace):

        return call_graph.build(workspace)

    def update(
        self,
        cache,
        workspace,
    ):

        cache._calls = self.build(workspace)


call_indexer = CallIndexer()
