from app.workspace.indexers.call_indexer import call_indexer
from app.workspace.indexers.graph_indexer import graph_indexer
from app.workspace.indexers.reference_indexer import reference_indexer
from app.workspace.indexers.resolver_indexer import resolver_indexer
from app.workspace.indexers.symbol_indexer import symbol_indexer


class IncrementalRebuilder:
    def rebuild(
        self,
        cache,
        changed_files,
        removed_files,
    ):

        rebuilt = []

        for file in changed_files:
            symbol_indexer.update(
                cache,
                file,
            )

            reference_indexer.update(
                cache,
                file,
            )

            rebuilt.append(file)

        for file in removed_files:
            symbol_indexer.remove(cache, file)
            reference_indexer.remove(cache, file)
            rebuilt.append(file)

        if rebuilt:
            graph_indexer.update(
                cache,
                cache.workspace,
            )
            resolver_indexer.update(
                cache,
                cache.workspace,
            )
            call_indexer.update(
                cache,
                cache.workspace,
            )

        return {
            "rebuilt": rebuilt,
            "symbols": len(cache.symbols()),
        }


incremental_rebuilder = IncrementalRebuilder()
