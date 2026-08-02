from app.workspace.graph import dependency_graph


class GraphIndexer:

    def build(
        self,
        workspace,
    ):
        return dependency_graph.build(workspace)

    def update(
        self,
        cache,
        workspace,
    ):
        cache._graph = dependency_graph.build(workspace)


graph_indexer = GraphIndexer()
