from app.workspace.references import reference_index


class ReferenceIndexer:
    def build(self, workspace):

        return reference_index.build(workspace)

    def update(
        self,
        cache,
        file,
    ):

        reference_index.update_file(
            cache._references,
            file,
            cache.workspace,
        )

    def remove(
        self,
        cache,
        file,
    ):

        reference_index.remove_file(
            cache._references,
            file,
        )


reference_indexer = ReferenceIndexer()
