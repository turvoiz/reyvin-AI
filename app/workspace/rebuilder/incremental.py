from app.workspace.indexers.resolver_indexer import resolver_indexer
from app.workspace.indexers.graph_indexer import graph_indexer
from app.workspace.indexers.symbol_indexer import symbol_indexer
from app.workspace.indexers.call_indexer import call_indexer
from app.workspace.indexers.reference_indexer import reference_indexer


class IncrementalRebuilder:

    def rebuild(
        self,
        cache,
        changed_files,
    ):

        print(f"[Incremental] {len(changed_files)} changed file(s)")

        rebuilt = []

        for file in changed_files:

            symbol_indexer.update(
                cache,
                file,
            )

            call_indexer.update(
                cache,
                cache.workspace,
            )

            graph_indexer.update(
                cache,
                cache.workspace,
            )

            reference_indexer.update(
                cache,
                file,
            )

            resolver_indexer.update(
                cache,
                cache.workspace,
            )

            print("[Symbol]", file)

            rebuilt.append(file)

        print("[Incremental] done")

        return {
            "rebuilt": rebuilt,
            "symbols": len(cache.symbols()),
        }


incremental_rebuilder = IncrementalRebuilder()