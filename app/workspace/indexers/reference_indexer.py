from app.workspace.reference_index import reference_index


class ReferenceIndexer:

    def build(self, workspace):

        return reference_index.build(workspace)

    def update(
        self,
        cache,
        workspace,
    ):

        cache._references = self.build(workspace)


reference_indexer = ReferenceIndexer()
