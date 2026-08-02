from app.workspace.resolver import resolver_index


class ResolverIndexer:
    def build(self, workspace):

        return resolver_index.build(workspace)

    def update(
        self,
        cache,
        workspace,
    ):

        cache._resolver = self.build(workspace)


resolver_indexer = ResolverIndexer()
